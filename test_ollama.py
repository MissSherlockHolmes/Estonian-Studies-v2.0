import requests
import json

# Test Ollama API directly
url = "http://deeperon2:11434/api/generate"
payload = {
    "model": "granite3.2-vision:latest",
    "prompt": "Hello, this is a test. Please respond with a short greeting.",
    "stream": False
}

print("Testing Ollama API...")
print(f"URL: {url}")
print(f"Payload: {payload}")

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Ollama API working!")
        print(f"Response: {result.get('response', 'No response')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
