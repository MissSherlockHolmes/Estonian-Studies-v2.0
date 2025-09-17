#!/usr/bin/env python3
"""
MD Prettifier for Estonian Studies
Uses ChatGPT to clean up and perfectly format markdown files
"""

import openai
import asyncio
import aiohttp
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv("config.env")

class MDPrettifier:
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass it as parameter.")
        openai.api_key = self.openai_api_key
    
    async def prettify_markdown(self, markdown_file: str, output_file: str = None) -> str:
        """
        Prettify a markdown file using ChatGPT
        
        Args:
            markdown_file: Path to input markdown file
            output_file: Path to output file (optional)
            
        Returns:
            Path to prettified markdown file
        """
        markdown_path = Path(markdown_file)
        
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        print(f"📖 Reading markdown file: {markdown_path.name}")
        
        # Read the markdown content
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📝 Content length: {len(content)} characters")
        
        # Split content into chunks if it's too long
        chunks = self.split_content_into_chunks(content)
        print(f"📦 Split into {len(chunks)} chunks for processing")
        
        # Process each chunk
        prettified_chunks = []
        for i, chunk in enumerate(chunks, 1):
            print(f"🔄 Processing chunk {i}/{len(chunks)}...")
            prettified_chunk = await self.prettify_chunk(chunk, i, len(chunks))
            prettified_chunks.append(prettified_chunk)
        
        # Combine all chunks
        final_content = "\n\n".join(prettified_chunks)
        
        # Post-process to clean up any remaining issues
        final_content = self.post_process_content(final_content)
        
        # Determine output file - create READ_Course_Name folder
        if output_file is None:
            # Find the course directory (parent of MD_Drafts folder)
            course_dir = markdown_path.parent.parent
            course_name = course_dir.name.replace(' ', '_')
            read_dir = course_dir / f"READ_{course_name}"
            read_dir.mkdir(exist_ok=True)
            output_file = read_dir / f"{markdown_path.stem}_prettified.md"
        else:
            output_file = Path(output_file)
        
        # Write prettified content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"✨ Prettified markdown saved to: {output_file}")
        return str(output_file)
    
    def split_content_into_chunks(self, content: str, max_chunk_size: int = 6000) -> List[str]:
        """Split content into manageable chunks for ChatGPT"""
        # Simple character-based splitting to ensure no content is lost
        chunks = []
        
        # Split by characters, trying to break at paragraph boundaries
        start = 0
        while start < len(content):
            end = start + max_chunk_size
            
            if end >= len(content):
                # Last chunk
                chunks.append(content[start:].strip())
                break
            
            # Try to find a good break point (end of paragraph)
            break_point = end
            for i in range(end, start + max_chunk_size // 2, -1):
                if content[i:i+2] == '\n\n':
                    break_point = i + 2
                    break
                elif content[i] == '\n':
                    break_point = i + 1
                    break
            
            chunks.append(content[start:break_point].strip())
            start = break_point
        
        return chunks
    
    def post_process_content(self, content: str) -> str:
        """Post-process content to clean up any remaining issues"""
        # Remove <doc> and </doc> tags
        content = re.sub(r'<doc>', '', content)
        content = re.sub(r'</doc>', '', content)
        
        # Remove markdown code blocks
        content = re.sub(r'```markdown\n?', '', content)
        content = re.sub(r'```\n?', '', content)
        
        # Clean up excessive bold formatting on author names
        content = re.sub(r'\*\*([A-Z][a-z]+ [A-Z][a-z]+)\*\*', r'\1', content)
        
        # Fix double line breaks
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Clean up any remaining formatting issues
        content = content.strip()
        
        return content
    
    async def prettify_chunk(self, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Prettify a single chunk using ChatGPT"""
        
        prompt = f"""You are an expert academic editor specializing in Estonian Studies and medieval history. Please clean up and perfectly format this markdown text while preserving ALL content.

CRITICAL REQUIREMENTS:
1. PRESERVE ALL TEXT - Do not remove or change any words, only fix typos , spacing, and formatting
2. FIX TYPOS - Correct obvious OCR errors and typos
3. IMPROVE HEADERS - Use proper markdown headers (# ## ### ####)
4. CLEAN FORMATTING - Fix spacing, line breaks, and markdown syntax
5. REMOVE MARKDOWN BLOCKS - Remove any ```markdown or ``` code blocks
6. REMOVE DOC TAGS - Remove <doc> and </doc> tags, they are not needed
7. ACADEMIC STYLE - Follow standard academic formatting conventions

FORMATTING RULES:
- Use ## for major chapter headers (Chapter 17, Introduction, etc.)
- Use ### for subsection headers
- Use *italics* for book titles and foreign words
- Use [^1]: for footnotes
- Separate paragraphs with blank lines
- Fix OCR errors like "che" → "the", "wich" → "which"
- Keep author names in normal text, not bold
- Use standard academic citation format

ACADEMIC STANDARDS:
- Book titles: *Chronicle of Henry of Livonia*
- Author names: Henry of Livonia (not bold)
- Page references: (p. 123)
- Footnotes: [^1]: Footnote text
- Clean, readable formatting without excessive emphasis

Please return the cleaned and formatted markdown text:"""

        try:
            response = await self.call_chatgpt(prompt, chunk)
            return response
        except Exception as e:
            print(f"⚠ Error processing chunk {chunk_num}: {e}")
            return chunk  # Return original if error
    
    async def call_chatgpt(self, prompt: str, content: str) -> str:
        """Call ChatGPT API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an expert academic editor specializing in Estonian Studies and medieval history."},
                {"role": "user", "content": f"{prompt}\n\n{content}"}
            ],
            "max_tokens": 12000,
            "temperature": 0.1
        }
        
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    raise Exception(f"ChatGPT API error: {response.status} - {error_text}")
    
    def process_directory(self, input_dir: str, output_dir: str = None) -> List[str]:
        """Process all markdown files in a directory"""
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Directory not found: {input_path}")
        
        # Find all markdown files
        md_files = list(input_path.glob("*.md"))
        if not md_files:
            print(f"No markdown files found in {input_path}")
            return []
        
        print(f"Found {len(md_files)} markdown files to prettify")
        
        processed_files = []
        for md_file in md_files:
            try:
                print(f"\n{'='*60}")
                print(f"Processing: {md_file.name}")
                print(f"{'='*60}")
                
                if output_dir:
                    output_path = Path(output_dir) / f"{md_file.stem}_prettified.md"
                else:
                    output_path = md_file.parent / f"{md_file.stem}_prettified.md"
                
                result = asyncio.run(self.prettify_markdown(str(md_file), str(output_path)))
                processed_files.append(result)
                print(f"✓ Successfully processed: {md_file.name}")
                
            except Exception as e:
                print(f"✗ Error processing {md_file.name}: {e}")
                continue
        
        return processed_files


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Prettify markdown files using ChatGPT")
    parser.add_argument("input", help="Input markdown file or directory")
    parser.add_argument("-o", "--output", help="Output file or directory")
    parser.add_argument("--api-key", help="OpenAI API key (optional if set in config.env)")
    
    args = parser.parse_args()
    
    prettifier = MDPrettifier(args.api_key)
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Process single file
        result = await prettifier.prettify_markdown(args.input, args.output)
        print(f"\n🎉 Successfully prettified: {result}")
    else:
        # Process directory
        results = prettifier.process_directory(args.input, args.output)
        print(f"\n🎉 Successfully processed {len(results)} files")


if __name__ == "__main__":
    asyncio.run(main())
