import requests
import json

# Test the PDF converter endpoint
url = "http://localhost:8000/pdf-converter"
data = {
    "pdf_path": "Nationalism and Transnational History\\PDFS_Nationalism_and_Transnational_History\\Hobsbawm, Invented Traditions.pdf",
    "extract_text": "true",
    "extract_tables": "true"
}

print("Testing PDF converter endpoint...")
print(f"URL: {url}")
print(f"Data: {data}")

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Extraction ID: {result.get('extraction_id')}")
        print(f"Message: {result.get('message')}")
        print(f"Processing Time: {result.get('processing_time')}s")
        
        if 'saved_files' in result:
            print("Saved Files:")
            for key, value in result['saved_files'].items():
                print(f"  {key}: {value}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
