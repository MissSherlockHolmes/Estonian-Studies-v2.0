#!/usr/bin/env python3
"""
Ollama Converter for Adobe PDF Services JSON Output
Takes Adobe PDF Services JSON output and converts it to formatted markdown using Ollama Granite
"""

import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime
from config import OLLAMA_URL, OLLAMA_MODEL


class OllamaConverter:
    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model = model or OLLAMA_MODEL
    
    async def query_ollama(self, prompt: str) -> str:
        """Query Ollama API with async aiohttp"""
        url = f"{self.ollama_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        print(f"Querying Ollama at: {url}")
        print(f"Using model: {self.model}")
        print(f"Prompt length: {len(prompt)} characters")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    print(f"Ollama response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Ollama error response: {error_text}")
                        return f"Ollama API error {response.status}: {error_text}"
                    
                    result = await response.json()
                    print(f"Ollama response keys: {result.keys()}")
                    
                    response_text = result.get("response", "No response content")
                    print(f"Ollama response length: {len(response_text)} characters")
                    print(f"Ollama response preview: {response_text[:200]}")
                    
                    return response_text
        
        except aiohttp.ClientError as e:
            error_msg = f"Error connecting to Ollama server: {str(e)}"
            print(error_msg)
            return error_msg
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding server response: {str(e)}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            return error_msg
    
    def extract_text_from_adobe_json(self, adobe_data: Dict[str, Any]) -> str:
        """
        Extract and structure text from Adobe PDF Services JSON data.
        
        Args:
            adobe_data: The structured document data from Adobe PDF Services
            
        Returns:
            Formatted text ready for Ollama processing
        """
        content_parts = []
        
        # Adobe PDF Services structure has 'elements' array
        if 'elements' in adobe_data:
            print(f"Found {len(adobe_data['elements'])} elements to process")
            
            for i, element in enumerate(adobe_data['elements']):
                # Extract text content
                if 'Text' in element and element['Text']:
                    text_content = element['Text'].strip()
                    if text_content:
                        # Get element path for context
                        path = element.get('Path', '')
                        
                        # Debug: print first few elements
                        if i < 10:
                            print(f"Element {i}: Path='{path}', Text='{text_content[:50]}...'")
                        
                        # Format based on element type
                        if 'Title' in path:
                            content_parts.append(f"\n# {text_content}\n")
                        elif 'H1' in path:
                            content_parts.append(f"\n# {text_content}\n")
                        elif 'H2' in path:
                            content_parts.append(f"\n## {text_content}\n")
                        elif 'H3' in path:
                            content_parts.append(f"\n### {text_content}\n")
                        elif 'List' in path:
                            content_parts.append(f"- {text_content}")
                        else:
                            # Regular paragraph text - just add the text
                            content_parts.append(text_content)
                
                # Handle table content
                elif 'Table' in element.get('Path', ''):
                    content_parts.append("\n[TABLE CONTENT]\n")
        
        # Join with single newlines to avoid too much spacing
        extracted_text = "\n".join(content_parts)
        print(f"Extracted text length: {len(extracted_text)} characters")
        print(f"First 500 chars: {extracted_text[:500]}")
        
        return extracted_text
    
    async def convert_to_markdown(self, adobe_data: Dict[str, Any], source_file: str) -> str:
        """
        Convert Adobe PDF Services JSON data to formatted markdown using Ollama.
        
        Args:
            adobe_data: The structured document data from Adobe PDF Services
            source_file: Original source file name for metadata
            
        Returns:
            Formatted markdown text
        """
        # Extract text from Adobe structure
        extracted_text = self.extract_text_from_adobe_json(adobe_data)
        
        # Process in chunks if the text is too long
        max_chunk_size = 15000  # Safe size for granite model
        if len(extracted_text) > max_chunk_size:
            print(f"Text too long ({len(extracted_text)} chars), processing in chunks...")
            return await self.convert_large_text_to_markdown(extracted_text, source_file)
        else:
            return await self.convert_single_chunk_to_markdown(extracted_text, source_file)
    
    async def convert_single_chunk_to_markdown(self, text: str, source_file: str) -> str:
        """Convert a single chunk of text to markdown"""
        prompt = f"""Convert this academic document text to clean markdown format:

FORMATTING RULES:
- Use # for main titles, ## for major sections, ### for subsections
- Use **bold** for emphasis and important terms
- Use *italic* for book titles and foreign words
- Use - for bullet points, 1. 2. 3. for numbered lists
- Add blank lines between paragraphs and sections
- Clean up OCR artifacts and fix spacing
- Preserve the logical structure and hierarchy

DOCUMENT TEXT:
{text}

Convert to markdown:"""

        # Query Ollama
        markdown_result = await self.query_ollama(prompt)
        
        # Add metadata header
        metadata = f"""---
title: "{Path(source_file).stem}"
source: "{Path(source_file).name}"
extracted_by: "Adobe PDF Services + Ollama Granite"
processed_date: "{datetime.now().isoformat()}"
---

"""
        
        return metadata + markdown_result
    
    async def convert_large_text_to_markdown(self, text: str, source_file: str) -> str:
        """Convert large text by processing in chunks"""
        chunk_size = 15000
        overlap = 1000  # Overlap to maintain context between chunks
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Find a good break point (end of paragraph)
                break_point = text.rfind('\n\n', start, end)
                if break_point > start + chunk_size // 2:
                    end = break_point
            
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap if end < len(text) else end
        
        print(f"Processing {len(chunks)} chunks...")
        
        # Process first chunk with full instructions
        first_chunk = chunks[0]
        prompt = f"""Convert this academic document text to clean markdown format:

FORMATTING RULES:
- Use # for main titles, ## for major sections, ### for subsections
- Use **bold** for emphasis and important terms
- Use *italic* for book titles and foreign words
- Use - for bullet points, 1. 2. 3. for numbered lists
- Add blank lines between paragraphs and sections
- Clean up OCR artifacts and fix spacing
- Preserve the logical structure and hierarchy

DOCUMENT TEXT (PART 1 of {len(chunks)}):
{first_chunk}

Convert to markdown:"""
        
        markdown_parts = [await self.query_ollama(prompt)]
        
        # Process remaining chunks
        for i, chunk in enumerate(chunks[1:], 2):
            prompt = f"""Continue converting this academic document text to markdown. This is part {i} of {len(chunks)}. Maintain the same formatting style as the previous parts:

DOCUMENT TEXT (PART {i} of {len(chunks)}):
{chunk}

Continue the markdown conversion:"""
            
            chunk_result = await self.query_ollama(prompt)
            markdown_parts.append(chunk_result)
        
        # Combine all parts
        full_markdown = "\n\n".join(markdown_parts)
        
        # Add metadata header
        metadata = f"""---
title: "{Path(source_file).stem}"
source: "{Path(source_file).name}"
extracted_by: "Adobe PDF Services + Ollama Granite (Chunked)"
processed_date: "{datetime.now().isoformat()}"
---

"""
        
        return metadata + full_markdown
    
    async def process_json_file(self, json_path: str, output_path: Optional[str] = None) -> str:
        """
        Process a single Adobe PDF Services JSON file and convert to markdown.
        
        Args:
            json_path: Path to the JSON file
            output_path: Path to save the markdown file (optional)
            
        Returns:
            Path to the saved markdown file
        """
        json_path = Path(json_path)
        
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        # Determine output file path - save to MD_Drafts in course directory
        if output_path:
            output_path = Path(output_path)
        else:
            # Find course directory (go up from adobe_output/extract_xxx/)
            course_dir = json_path.parent.parent.parent
            md_drafts_dir = course_dir / "MD_Drafts"
            md_drafts_dir.mkdir(exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{json_path.stem}_{timestamp}.md"
            output_path = md_drafts_dir / output_filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            adobe_data = json.load(f)
        
        # Convert to markdown
        markdown_content = await self.convert_to_markdown(adobe_data, json_path.stem)
        
        # Save markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✓ Successfully converted: {json_path.name}")
        print(f"✓ Markdown saved to: {output_path}")
        
        return str(output_path)


async def main():
    parser = argparse.ArgumentParser(description="Convert Adobe PDF Services JSON to markdown using Ollama")
    parser.add_argument("input", help="Input JSON file or directory")
    parser.add_argument("-o", "--output", help="Output file or directory")
    parser.add_argument("-r", "--recursive", action="store_true",
                       help="Process JSONs recursively in subdirectories")
    parser.add_argument("--ollama-url", default=OLLAMA_URL,
                       help="Ollama server URL")
    parser.add_argument("--model", default=OLLAMA_MODEL,
                       help="Ollama model to use")
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = OllamaConverter(args.ollama_url, args.model)
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        if input_path.suffix.lower() != '.json':
            print("Error: Input file must be a JSON file")
            exit(1)
        
        try:
            result = await converter.process_json_file(input_path, args.output)
            print(f"Successfully processed: {result}")
        except Exception as e:
            print(f"Error: {e}")
            exit(1)
    
    elif input_path.is_dir():
        try:
            results = await converter.process_directory(input_path, args.output, args.recursive)
            print(f"Successfully processed {len(results)} files")
        except Exception as e:
            print(f"Error: {e}")
            exit(1)
    
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
