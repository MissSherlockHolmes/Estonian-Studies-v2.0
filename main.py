"""
PDF Content Extraction API using Adobe PDF Services SDK
FastAPI endpoint for extracting text, tables, and images from PDF files
"""

import logging
import os
import tempfile
import zipfile
import json
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO
from config import validate_config, PDF_SERVICES_CLIENT_ID, PDF_SERVICES_CLIENT_SECRET
from ollama_converter import OllamaConverter
from gpt_converter import MDPrettifier
from note_taker import NoteTaker

# Validate configuration
validate_config()

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="PDF Content Extraction API",
    description="Extract text, tables, and images from PDF files using Adobe PDF Services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving documents
app.mount("/static", StaticFiles(directory="."), name="static")

# Response models
class ExtractionResponse(BaseModel):
    success: bool
    message: str
    extraction_id: str
    structured_data: Optional[Dict[Any, Any]] = None
    renditions_info: Optional[Dict[str, Any]] = None
    saved_files: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None

class ErrorResponse(BaseModel):
    success: bool
    error: str
    details: Optional[str] = None

# PDF Services configuration
def get_pdf_services():
    """Initialize PDF Services with credentials"""
    try:
        credentials = ServicePrincipalCredentials(
            client_id=PDF_SERVICES_CLIENT_ID,
            client_secret=PDF_SERVICES_CLIENT_SECRET
        )
        return PDFServices(credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize PDF Services: {e}")
        raise HTTPException(status_code=500, detail="PDF Services initialization failed")

def extract_content_from_zip(zip_content: bytes, extraction_id: str, original_filename: str, pdf_path: str) -> Dict[str, Any]:
    """Extract and parse content from the ZIP response, saving files to disk"""
    import os
    from pathlib import Path
    
    result = {
        "structured_data": None,
        "renditions_info": {
            "tables": [],
            "figures": []
        },
        "saved_files": {
            "output_directory": None,
            "json_file": None,
            "rendition_files": []
        }
    }
    
    try:
        # Determine the course directory from the PDF path
        pdf_path_obj = Path(pdf_path)
        course_dir = pdf_path_obj.parent.parent  # Go up from PDFS_Course_Name to Course_Name
        
        # Create adobe_output directory within the course
        output_dir = course_dir / "adobe_output" / extraction_id
        output_dir.mkdir(parents=True, exist_ok=True)
        result["saved_files"]["output_directory"] = str(output_dir)
        
        logger.info(f"Saving extraction results to: {output_dir}")
        
        with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
            # Extract and save structured data JSON
            if 'structuredData.json' in zip_file.namelist():
                with zip_file.open('structuredData.json') as json_file:
                    structured_data = json.load(json_file)
                    result["structured_data"] = structured_data
                    
                    # Save JSON file to disk
                    json_filename = f"{original_filename.replace('.pdf', '')}_extracted.json"
                    json_path = output_dir / json_filename
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(structured_data, f, indent=2, ensure_ascii=False)
                    result["saved_files"]["json_file"] = str(json_path)
                    logger.info(f"Saved structured data to: {json_path}")
            
            # Extract and save rendition files
            for file_name in zip_file.namelist():
                if file_name.startswith('tables/') or file_name.startswith('figures/'):
                    # Extract the file
                    file_data = zip_file.read(file_name)
                    
                    # Save to output directory
                    output_file_path = output_dir / file_name
                    output_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_file_path, 'wb') as f:
                        f.write(file_data)
                    
                    result["saved_files"]["rendition_files"].append(str(output_file_path))
                    
                    # Add to appropriate category
                    if file_name.startswith('tables/'):
                        result["renditions_info"]["tables"].append(file_name)
                    elif file_name.startswith('figures/'):
                        result["renditions_info"]["figures"].append(file_name)
                        
                    logger.info(f"Saved rendition file: {output_file_path}")
    
    except Exception as e:
        logger.error(f"Error extracting ZIP content: {e}")
        raise HTTPException(status_code=500, detail="Failed to process extraction results")
    
    return result

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PDF Content Extraction API is running", "status": "healthy"}

@app.get("/pdfs")
async def list_pdfs():
    """Get list of available PDFs organized by course"""
    import os
    import glob
    from pathlib import Path
    
    base_path = Path(".")
    courses = {}
    
    # Define course directories
    course_mappings = {
        "Estonian Regional Studies": "estonian-regional-studies",
        "Introduction to Estonian Studies": "introduction-to-estonian-studies", 
        "Key Conceots in Cultural Analysis": "key-concepts-cultural-analysis",
        "Language and Society": "language-and-society",
        "Nationalism and Transnational History": "nationalism-transnational-history"
    }
    
    try:
        for course_name, course_id in course_mappings.items():
            course_path = base_path / course_name / f"PDFS_{course_name.replace(' ', '_')}"
            if course_path.exists():
                pdf_files = list(course_path.glob("*.pdf"))
                courses[course_id] = {
                    "name": course_name,
                    "pdfs": []
                }
                
                for pdf_file in pdf_files:
                    try:
                        file_size = pdf_file.stat().st_size
                        courses[course_id]["pdfs"].append({
                            "name": pdf_file.name,
                            "path": str(pdf_file.relative_to(base_path)),
                            "size": file_size,
                            "size_formatted": format_file_size(file_size)
                        })
                    except Exception as e:
                        logger.warning(f"Error processing file {pdf_file}: {e}")
                        continue
        
        # Add Adobe samples as a test course
        adobe_path = base_path / "PDFServicesSDK-PythonSamples" / "adobe-dc-pdf-services-sdk-python" / "src" / "resources"
        if adobe_path.exists():
            pdf_files = list(adobe_path.glob("*.pdf"))
            if pdf_files:
                courses["adobe-samples"] = {
                    "name": "Adobe PDF Samples",
                    "pdfs": []
                }
                
                for pdf_file in pdf_files:
                    try:
                        file_size = pdf_file.stat().st_size
                        courses["adobe-samples"]["pdfs"].append({
                            "name": pdf_file.name,
                            "path": str(pdf_file.relative_to(base_path)),
                            "size": file_size,
                            "size_formatted": format_file_size(file_size)
                        })
                    except Exception as e:
                        logger.warning(f"Error processing Adobe file {pdf_file}: {e}")
                        continue
        
        return {"success": True, "courses": courses}
        
    except Exception as e:
        logger.error(f"Error listing PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list PDFs: {str(e)}")

@app.get("/documents")
async def list_documents():
    """Get list of all available documents (PDFs, DOCX, PPTX) organized by course"""
    import os
    import glob
    from pathlib import Path
    
    base_path = Path(".")
    courses = {}
    
    # Define course directories and their document subdirectories
    course_mappings = {
        "Estonian Regional Studies": "estonian-regional-studies",
        "Introduction to Estonian Studies": "introduction-to-estonian-studies", 
        "Key Conceots in Cultural Analysis": "key-concepts-cultural-analysis",
        "Language and Society": "language-and-society",
        "Nationalism and Transnational History": "nationalism-transnational-history"
    }
    
    # Document subdirectories to search - PDFS subdirectories and main course directories
    doc_subdirs = {
        "pdfs": "PDFS_{course_name}",
        "main": ""  # Main course directory for DOCX/PPTX files
    }
    
    # File extensions and their types
    file_types = {
        ".pdf": "pdf",
        ".docx": "docx", 
        ".doc": "docx",
        ".pptx": "pptx",
        ".ppt": "pptx"
    }
    
    try:
        for course_name, course_id in course_mappings.items():
            courses[course_id] = {
                "name": course_name,
                "documents": []
            }
            
            # Search in PDFS subdirectories and main course directories
            for subdir_type, subdir_pattern in doc_subdirs.items():
                if subdir_pattern:  # PDFS subdirectories
                    subdir_name = subdir_pattern.format(course_name=course_name.replace(' ', '_'))
                    course_path = base_path / course_name / subdir_name
                else:  # Main course directory
                    course_path = base_path / course_name
                
                if course_path.exists():
                    # Find all supported document types
                    for ext, doc_type in file_types.items():
                        files = list(course_path.glob(f"*{ext}"))
                        
                        for file_path in files:
                            try:
                                file_size = file_path.stat().st_size
                                # Normalize path separators for URLs
                                relative_path = str(file_path.relative_to(base_path)).replace('\\', '/')
                                courses[course_id]["documents"].append({
                                    "name": file_path.name,
                                    "path": relative_path,
                                    "size": file_size,
                                    "size_formatted": format_file_size(file_size),
                                    "type": doc_type,
                                    "subdirectory": subdir_type
                                })
                            except Exception as e:
                                logger.warning(f"Error processing file {file_path}: {e}")
                                continue
        
        # Add Adobe samples as a test course
        adobe_path = base_path / "PDFServicesSDK-PythonSamples" / "adobe-dc-pdf-services-sdk-python" / "src" / "resources"
        if adobe_path.exists():
            pdf_files = list(adobe_path.glob("*.pdf"))
            if pdf_files:
                courses["adobe-samples"] = {
                    "name": "Adobe PDF Samples",
                    "documents": []
                }
                
                for pdf_file in pdf_files:
                    try:
                        file_size = pdf_file.stat().st_size
                        # Normalize path separators for URLs
                        relative_path = str(pdf_file.relative_to(base_path)).replace('\\', '/')
                        courses["adobe-samples"]["documents"].append({
                            "name": pdf_file.name,
                            "path": relative_path,
                            "size": file_size,
                            "size_formatted": format_file_size(file_size),
                            "type": "pdf",
                            "subdirectory": "samples"
                        })
                    except Exception as e:
                        logger.warning(f"Error processing Adobe file {pdf_file}: {e}")
                        continue
        
        return {"success": True, "courses": courses}
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.get("/documents/{file_path:path}")
async def serve_document(file_path: str):
    """Serve a document file"""
    from pathlib import Path
    import urllib.parse
    
    # Decode URL-encoded path and normalize path separators for Windows
    decoded_path = urllib.parse.unquote(file_path)
    # Convert forward slashes back to backslashes for Windows file system
    normalized_path = decoded_path.replace('/', '\\') if os.name == 'nt' else decoded_path
    full_path = Path(normalized_path)
    
    logger.info(f"Serving document: original_path='{file_path}', decoded='{decoded_path}', normalized='{normalized_path}', full_path='{full_path}'")
    
    # Check if file exists
    if not full_path.exists():
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {full_path}")
    
    # Check if it's a supported document type
    allowed_extensions = {'.pdf', '.docx', '.doc', '.pptx', '.ppt'}
    if full_path.suffix.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Determine appropriate media type
    media_type_mapping = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.ppt': 'application/vnd.ms-powerpoint'
    }
    
    media_type = media_type_mapping.get(full_path.suffix.lower(), 'application/octet-stream')
    
    # For PDFs, use streaming response to force inline display
    if full_path.suffix.lower() == '.pdf':
        from fastapi.responses import StreamingResponse
        import io
        
        def generate():
            with open(full_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            generate(),
            media_type='application/pdf',
            headers={
                'Content-Disposition': 'inline',
                'Cache-Control': 'no-cache',
                'X-Content-Type-Options': 'nosniff'
            }
        )
    else:
        # For other files (DOCX, PPTX), return with headers optimized for online viewers
        response = FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type=media_type
        )
        
        # Headers optimized for online document viewers
        response.headers["Content-Disposition"] = f'inline; filename="{full_path.name}"'
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept, Origin"
        response.headers["Cache-Control"] = "public, max-age=3600"
        
        return response

@app.get("/docx-viewer/{file_path:path}")
async def docx_viewer(file_path: str):
    """Serve DOCX files specifically for inline viewing"""
    from pathlib import Path
    import urllib.parse
    from fastapi.responses import StreamingResponse
    
    # Decode URL-encoded path and normalize path separators for Windows
    decoded_path = urllib.parse.unquote(file_path)
    normalized_path = decoded_path.replace('/', '\\') if os.name == 'nt' else decoded_path
    full_path = Path(normalized_path)
    
    logger.info(f"DOCX viewer request: {full_path}")
    
    # Check if file exists and is a DOCX
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="DOCX file not found")
    
    if full_path.suffix.lower() not in ['.docx', '.doc']:
        raise HTTPException(status_code=400, detail="File is not a DOCX document")
    
    # Stream the DOCX with headers that allow inline viewing
    def generate():
        with open(full_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        generate(),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': 'inline',
            'Cache-Control': 'no-cache',
            'X-Content-Type-Options': 'nosniff',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

@app.get("/pptx-viewer/{file_path:path}")
async def pptx_viewer(file_path: str):
    """Serve PPTX files specifically for inline viewing"""
    from pathlib import Path
    import urllib.parse
    from fastapi.responses import StreamingResponse
    
    # Decode URL-encoded path and normalize path separators for Windows
    decoded_path = urllib.parse.unquote(file_path)
    normalized_path = decoded_path.replace('/', '\\') if os.name == 'nt' else decoded_path
    full_path = Path(normalized_path)
    
    logger.info(f"PPTX viewer request: {full_path}")
    
    # Check if file exists and is a PPTX
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="PPTX file not found")
    
    if full_path.suffix.lower() not in ['.pptx', '.ppt']:
        raise HTTPException(status_code=400, detail="File is not a PPTX presentation")
    
    # Stream the PPTX with headers that allow inline viewing
    def generate():
        with open(full_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        generate(),
        media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        headers={
            'Content-Disposition': 'inline',
            'Cache-Control': 'no-cache',
            'X-Content-Type-Options': 'nosniff',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

@app.options("/documents/{file_path:path}")
async def documents_options(file_path: str):
    """Handle CORS preflight requests for document serving"""
    from fastapi.responses import Response
    
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept, Origin, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

@app.get("/pdf-viewer/{file_path:path}")
async def pdf_viewer(file_path: str):
    """Serve PDF files specifically for inline viewing (no download)"""
    from pathlib import Path
    import urllib.parse
    from fastapi.responses import StreamingResponse
    
    # Decode URL-encoded path and normalize path separators for Windows
    decoded_path = urllib.parse.unquote(file_path)
    normalized_path = decoded_path.replace('/', '\\') if os.name == 'nt' else decoded_path
    full_path = Path(normalized_path)
    
    logger.info(f"PDF viewer request: {full_path}")
    
    # Check if file exists and is a PDF
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    if full_path.suffix.lower() != '.pdf':
        raise HTTPException(status_code=400, detail="File is not a PDF")
    
    # Stream the PDF with headers that prevent download
    def generate():
        with open(full_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        generate(),
        media_type='application/pdf',
        headers={
            'Content-Disposition': 'inline',
            'Content-Type': 'application/pdf',
            'Cache-Control': 'no-cache',
            'X-Content-Type-Options': 'nosniff',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

@app.post("/pdf-converter", response_model=ExtractionResponse)
async def extract_pdf_content(
    file: UploadFile = File(None),
    pdf_path: Optional[str] = Form(None),
    extract_text: bool = Form(True),
    extract_tables: bool = Form(True),
    extract_figures: bool = Form(True),
    include_styling: bool = Form(False),
    include_char_bounds: bool = Form(False)
):
    """
    Extract content from PDF file
    
    Parameters:
    - file: PDF file to process
    - extract_text: Extract text elements (default: True)
    - extract_tables: Extract table elements (default: True) 
    - extract_figures: Extract figure elements (default: True)
    - include_styling: Include styling information (default: False)
    - include_char_bounds: Include character bounding boxes (default: False)
    """
    
    start_time = datetime.now()
    extraction_id = f"extract_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Log the received parameters for debugging
        logger.info(f"Received parameters: file={file}, pdf_path={pdf_path}")
        
        # Handle either uploaded file or file path
        if file is not None and file.filename:
            # Validate file type for uploaded file
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            # Read the uploaded file
            pdf_content = await file.read()
            filename = file.filename
            logger.info(f"Processing uploaded PDF: {filename} ({len(pdf_content)} bytes)")
            
        elif pdf_path is not None and pdf_path.strip():
            # Read file from path
            from pathlib import Path
            file_path = Path(pdf_path)
            
            if not file_path.exists():
                logger.error(f"PDF file not found at path: {pdf_path}")
                raise HTTPException(status_code=400, detail=f"PDF file not found: {pdf_path}")
            
            if not file_path.suffix.lower() == '.pdf':
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
            filename = file_path.name
            logger.info(f"Processing PDF from path: {pdf_path} -> {filename} ({len(pdf_content)} bytes)")
            
        else:
            logger.error(f"No valid input provided: file={file}, pdf_path='{pdf_path}'")
            raise HTTPException(status_code=400, detail="Either file upload or pdf_path must be provided")
        
        # Initialize PDF Services
        pdf_services = get_pdf_services()
        
        # Upload the PDF
        input_asset = pdf_services.upload(input_stream=pdf_content, mime_type=PDFServicesMediaType.PDF)
        
        # Build extraction parameters
        elements_to_extract = []
        renditions_to_extract = []
        
        if extract_text:
            elements_to_extract.append(ExtractElementType.TEXT)
        if extract_tables:
            elements_to_extract.append(ExtractElementType.TABLES)
            renditions_to_extract.append(ExtractRenditionsElementType.TABLES)
        
        # For figures, we only extract renditions (not element content)
        if extract_figures:
            renditions_to_extract.append(ExtractRenditionsElementType.FIGURES)
        
        if not elements_to_extract:
            raise HTTPException(status_code=400, detail="At least one extraction type must be selected")
        
        logger.info(f"Elements to extract: {elements_to_extract}")
        logger.info(f"Renditions to extract: {renditions_to_extract}")
        
        # Create extraction parameters
        extract_pdf_params_dict = {
            "elements_to_extract": elements_to_extract,
        }
        
        # Add optional parameters only if they are True
        if include_styling:
            extract_pdf_params_dict["styling_info"] = True
        if include_char_bounds:
            extract_pdf_params_dict["add_char_info"] = True
        if renditions_to_extract:
            extract_pdf_params_dict["elements_to_extract_renditions"] = renditions_to_extract
            
        logger.info(f"ExtractPDFParams: {extract_pdf_params_dict}")
        extract_pdf_params = ExtractPDFParams(**extract_pdf_params_dict)
        
        # Create and submit job
        extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
        location = pdf_services.submit(extract_pdf_job)
        pdf_services_response = pdf_services.get_job_result(location, ExtractPDFResult)
        
        # Get the result
        result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
        stream_asset: StreamAsset = pdf_services.get_content(result_asset)
        zip_content = stream_asset.get_input_stream()
        
        # Extract content from ZIP and save to disk
        extracted_content = extract_content_from_zip(zip_content, extraction_id, filename, pdf_path if pdf_path else "general")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Successfully processed {filename} in {processing_time:.2f}s")
        
        # Create markdown conversion using Ollama (optional)
        markdown_file = None
        try:
            if extracted_content["structured_data"]:
                logger.info("Starting Ollama markdown conversion...")
                converter = OllamaConverter()
                
                # Determine course directory and create MD_Drafts folder
                pdf_path_obj = Path(pdf_path) if pdf_path else Path("general")
                course_dir = pdf_path_obj.parent.parent if pdf_path else Path(".")
                md_drafts_dir = course_dir / "MD_Drafts"
                md_drafts_dir.mkdir(exist_ok=True)
                
                # Create markdown filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                md_filename = f"{filename.replace('.pdf', '')}_{timestamp}.md"
                md_path = md_drafts_dir / md_filename
                
                # Convert to markdown
                logger.info("Calling Ollama for markdown conversion...")
                markdown_content = await converter.convert_to_markdown(
                    extracted_content["structured_data"], 
                    filename
                )
                
                # Validate markdown content
                if len(markdown_content.strip()) < 100:
                    logger.warning(f"Markdown content seems too short: {len(markdown_content)} chars")
                    logger.warning(f"Content preview: {markdown_content[:200]}")
                
                # Save markdown file
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                markdown_file = str(md_path)
                logger.info(f"Saved markdown to: {md_path} ({len(markdown_content)} chars)")
                
        except Exception as e:
            logger.error(f"Markdown conversion failed: {e}")
            import traceback
            logger.error(f"Full error: {traceback.format_exc()}")
        
        # Add markdown file to saved_files
        if markdown_file:
            extracted_content["saved_files"]["markdown_file"] = markdown_file
        
        # Create prettified markdown using GPT (optional)
        prettified_file = None
        try:
            if markdown_file:
                logger.info("Starting GPT markdown prettification...")
                prettifier = MDPrettifier()
                
                # Determine course directory and create READ folder
                pdf_path_obj = Path(pdf_path) if pdf_path else Path("general")
                course_dir = pdf_path_obj.parent.parent if pdf_path else Path(".")
                read_dir = course_dir / f"READ_{course_dir.name.replace(' ', '_')}"
                read_dir.mkdir(exist_ok=True)
                
                # Create prettified filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prettified_filename = f"{filename.replace('.pdf', '')}_prettified_{timestamp}.md"
                prettified_path = read_dir / prettified_filename
                
                # Prettify the markdown
                logger.info("Calling GPT for markdown prettification...")
                prettified_file = await prettifier.prettify_markdown(
                    markdown_file, 
                    str(prettified_path)
                )
                
                logger.info(f"Saved prettified markdown to: {prettified_file}")
                
        except Exception as e:
            logger.error(f"GPT prettification failed: {e}")
            import traceback
            logger.error(f"Full error: {traceback.format_exc()}")
        
        # Add prettified file to saved_files
        if prettified_file:
            extracted_content["saved_files"]["prettified_file"] = prettified_file
        
        return ExtractionResponse(
            success=True,
            message="PDF content extracted successfully" + 
                   (" with markdown conversion" if markdown_file else "") +
                   (" and prettification" if prettified_file else ""),
            extraction_id=extraction_id,
            structured_data=extracted_content["structured_data"],
            renditions_info=extracted_content["renditions_info"],
            saved_files=extracted_content["saved_files"],
            processing_time=processing_time
        )
        
    except (ServiceApiException, ServiceUsageException) as e:
        logger.error(f"Adobe PDF Services error: {e}")
        raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")
    
    except SdkException as e:
        logger.error(f"SDK error: {e}")
        raise HTTPException(status_code=500, detail=f"SDK error: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/pdf-converter/text-only", response_model=ExtractionResponse)
async def extract_text_only(file: UploadFile = File(...)):
    """
    Extract only text content from PDF (faster for text-only extraction)
    """
    return await extract_pdf_content(
        file=file,
        extract_text=True,
        extract_tables=False,
        extract_figures=False,
        include_styling=False,
        include_char_bounds=False
    )

@app.post("/pdf-converter/with-tables", response_model=ExtractionResponse)
async def extract_with_tables(file: UploadFile = File(...)):
    """
    Extract text and tables from PDF with renditions
    """
    return await extract_pdf_content(
        file=file,
        extract_text=True,
        extract_tables=True,
        extract_figures=False,
        include_styling=False,
        include_char_bounds=False
    )

@app.post("/pdf-converter/comprehensive", response_model=ExtractionResponse)
async def extract_comprehensive(file: UploadFile = File(...)):
    """
    Comprehensive extraction: text, tables, figures with styling and character bounds
    """
    return await extract_pdf_content(
        file=file,
        extract_text=True,
        extract_tables=True,
        extract_figures=True,
        include_styling=True,
        include_char_bounds=True
    )

# Note-taking endpoints
note_taker = NoteTaker()

@app.get("/notes/files")
async def list_markdown_files():
    """Get list of all markdown files available for note-taking"""
    from pathlib import Path
    import glob
    
    base_path = Path(".")
    markdown_files = []
    
    # Search in READ_ directories for prettified markdown files
    read_dirs = list(base_path.glob("*/READ_*"))
    
    for read_dir in read_dirs:
        if read_dir.is_dir():
            course_name = read_dir.parent.name
            md_files = list(read_dir.glob("*.md"))
            
            for md_file in md_files:
                try:
                    file_size = md_file.stat().st_size
                    markdown_files.append({
                        "name": md_file.name,
                        "path": str(md_file.relative_to(base_path)).replace('\\', '/'),
                        "course": course_name,
                        "size": file_size,
                        "size_formatted": format_file_size(file_size),
                        "modified": md_file.stat().st_mtime
                    })
                except Exception as e:
                    logger.warning(f"Error processing markdown file {md_file}: {e}")
                    continue
    
    # Sort by modification time (newest first)
    markdown_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return {"success": True, "files": markdown_files}

@app.post("/notes/add")
async def add_note(
    file_path: str = Form(...),
    search_term: str = Form(""),
    note_text: str = Form(...),
    note_type: str = Form("note"),
    color: str = Form("yellow")
):
    """Add a note to a markdown file"""
    try:
        from pathlib import Path
        # Normalize path separators for Windows
        normalized_path = file_path.replace('/', '\\') if os.name == 'nt' else file_path
        full_path = Path(normalized_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Markdown file not found")
        
        success = note_taker.add_note_to_file(
            str(full_path), 
            search_term, 
            note_text, 
            note_type, 
            color
        )
        
        if success:
            return {"success": True, "message": "Note added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add note")
            
    except Exception as e:
        logger.error(f"Error adding note: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add note: {str(e)}")

@app.get("/notes/list/{file_path:path}")
async def list_notes(file_path: str):
    """List all notes in a markdown file"""
    try:
        from pathlib import Path
        # Normalize path separators for Windows
        normalized_path = file_path.replace('/', '\\') if os.name == 'nt' else file_path
        full_path = Path(normalized_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Markdown file not found")
        
        notes = note_taker.list_notes_in_file(str(full_path))
        
        return {
            "success": True, 
            "file": file_path,
            "notes": [
                {
                    "index": i + 1,
                    "type": note[0],
                    "timestamp": note[1], 
                    "text": note[2]
                } 
                for i, note in enumerate(notes)
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list notes: {str(e)}")

@app.delete("/notes/delete")
async def delete_note(
    file_path: str = Form(...),
    note_index: int = Form(...)
):
    """Delete a note from a markdown file"""
    try:
        from pathlib import Path
        # Normalize path separators for Windows
        normalized_path = file_path.replace('/', '\\') if os.name == 'nt' else file_path
        full_path = Path(normalized_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Markdown file not found")
        
        success = note_taker.delete_note_from_file(str(full_path), note_index)
        
        if success:
            return {"success": True, "message": "Note deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete note")
            
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")

@app.get("/notes/content/{file_path:path}")
async def get_file_content(file_path: str):
    """Get the content of a markdown file for preview"""
    try:
        from pathlib import Path
        # Normalize path separators for Windows
        normalized_path = file_path.replace('/', '\\') if os.name == 'nt' else file_path
        full_path = Path(normalized_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Markdown file not found")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "file": file_path,
            "content": content,
            "full_length": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file content: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
