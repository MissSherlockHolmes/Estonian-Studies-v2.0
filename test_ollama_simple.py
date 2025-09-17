import requests
import json

# Test Ollama with a simple prompt
url = "http://deeperon2:11434/api/generate"
payload = {
    "model": "granite3.2-vision:latest",
    "prompt": "Convert this text to markdown: Contributors\nI\nDAVID CANNADINE is Professor of History at Columbia University.",
    "stream": False
}

print("Testing Ollama with simple prompt...")
print(f"URL: {url}")

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Ollama working!")
        print(f"Response: {result.get('response', 'No response')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
