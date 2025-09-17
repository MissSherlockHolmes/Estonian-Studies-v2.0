import json
import asyncio
from ollama_converter import OllamaConverter

async def test_ollama_with_existing_json():
    """Test Ollama conversion using existing JSON file to avoid Adobe API calls"""
    
    # Load existing JSON file
    json_path = "Nationalism and Transnational History/adobe_output/extract_20250917_202206/Hobsbawm, Invented Traditions_extracted.json"
    
    print(f"Loading JSON from: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        adobe_data = json.load(f)
    
    print(f"Loaded JSON with {len(adobe_data.get('elements', []))} elements")
    
    # Test Ollama conversion
    converter = OllamaConverter()
    
    print("Converting to markdown...")
    markdown_content = await converter.convert_to_markdown(adobe_data, "Hobsbawm, Invented Traditions.pdf")
    
    print(f"Generated markdown length: {len(markdown_content)} characters")
    print(f"First 500 characters:")
    print(markdown_content[:500])
    print("\n" + "="*50)
    print("Last 500 characters:")
    print(markdown_content[-500:])
    
    # Save to test file
    with open("test_ollama_output.md", 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\nSaved full output to: test_ollama_output.md")

if __name__ == "__main__":
    asyncio.run(test_ollama_with_existing_json())
