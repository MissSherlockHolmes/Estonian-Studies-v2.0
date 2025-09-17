#!/usr/bin/env python3
"""
Test script for GPT prettifier using existing markdown file
"""

import asyncio
import json
from pathlib import Path
from gpt_converter import MDPrettifier

async def test_gpt_prettifier():
    """Test GPT prettifier using existing markdown file"""
    
    # Find the most recent markdown file
    md_drafts_dir = Path("Nationalism and Transnational History/MD_Drafts")
    if not md_drafts_dir.exists():
        print("Error: MD_Drafts directory not found")
        return
    
    # Get the most recent markdown file
    md_files = list(md_drafts_dir.glob("*.md"))
    if not md_files:
        print("Error: No markdown files found in MD_Drafts")
        return
    
    # Sort by modification time and get the most recent
    latest_md = max(md_files, key=lambda x: x.stat().st_mtime)
    print(f"Using markdown file: {latest_md}")
    
    try:
        prettifier = MDPrettifier()
        
        print("Starting GPT prettification...")
        prettified_file = await prettifier.prettify_markdown(str(latest_md))
        
        print(f"✅ Successfully prettified markdown!")
        print(f"📁 Input: {latest_md}")
        print(f"📁 Output: {prettified_file}")
        
        # Show file sizes
        input_size = latest_md.stat().st_size
        output_size = Path(prettified_file).stat().st_size
        print(f"📊 Input size: {input_size:,} characters")
        print(f"📊 Output size: {output_size:,} characters")
        
        # Show preview of prettified content
        with open(prettified_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📖 Preview of prettified content (first 500 chars):")
        print("=" * 60)
        print(content[:500])
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_gpt_prettifier())
