"""
Simple test script for the PDF Content Extraction API
"""

import requests
import json
import os

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_pdf_extraction(pdf_file_path, endpoint="/pdf-converter/text-only"):
    """Test PDF extraction endpoint"""
    if not os.path.exists(pdf_file_path):
        print(f"PDF file not found: {pdf_file_path}")
        return
    
    print(f"Testing PDF extraction with {endpoint}...")
    print(f"File: {pdf_file_path}")
    
    try:
        with open(pdf_file_path, 'rb') as f:
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                files={'file': f},
                timeout=60  # 60 second timeout
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Extraction ID: {result.get('extraction_id')}")
            print(f"Processing Time: {result.get('processing_time')} seconds")
            
            # Print some basic info about extracted content
            if result.get('structured_data'):
                elements = result['structured_data'].get('elements', [])
                print(f"Extracted {len(elements)} elements")
                
                # Count element types
                element_types = {}
                for element in elements:
                    elem_type = element.get('Path', 'unknown')
                    element_types[elem_type] = element_types.get(elem_type, 0) + 1
                
                print("Element types:", element_types)
            
            if result.get('renditions_info'):
                tables = result['renditions_info'].get('tables', [])
                figures = result['renditions_info'].get('figures', [])
                print(f"Table renditions: {len(tables)}")
                print(f"Figure renditions: {len(figures)}")
        else:
            print("❌ Error!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 50)

def main():
    """Main test function"""
    print("PDF Content Extraction API Test")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Look for test PDF files
    test_files = [
        # From Adobe samples
        "PDFServicesSDK-PythonSamples/adobe-dc-pdf-services-sdk-python/src/resources/extractPdfInput.pdf",
        "PDFServicesSDK-PythonSamples/adobe-dc-pdf-services-sdk-python/src/resources/exportPDFInput.pdf",
        # Common names
        "test.pdf",
        "sample.pdf",
        "document.pdf"
    ]
    
    pdf_found = False
    for pdf_file in test_files:
        if os.path.exists(pdf_file):
            pdf_found = True
            print(f"Found test PDF: {pdf_file}")
            
            # Test different endpoints
            test_pdf_extraction(pdf_file, "/pdf-converter/text-only")
            test_pdf_extraction(pdf_file, "/pdf-converter/with-tables")
            break
    
    if not pdf_found:
        print("No test PDF files found. Please provide a PDF file to test.")
        print("Expected locations:")
        for pdf_file in test_files:
            print(f"  - {pdf_file}")

if __name__ == "__main__":
    main()
