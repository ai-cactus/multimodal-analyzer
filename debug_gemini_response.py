"""Test Gemini REST API response parsing"""
import requests
import json
from app.config import get_settings
import subprocess

def test_gemini_response():
    settings = get_settings()
    
    # Get token
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True,
        check=True
    )
    token = result.stdout.strip()
    
    endpoint = f"https://aiplatform.googleapis.com/v1/projects/{settings.gcp_project_id}/locations/{settings.gemini_region}/publishers/google/models/gemini-3-flash-preview:streamGenerateContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": {
            "role": "user",
            "parts": [{"text": "Say 'Hello!' and nothing else"}]
        },
        "generation_config": {
            "maxOutputTokens": 50,
            "temperature": 0.1
        }
    }
    
    print("Testing Gemini API...")
    print(f"Endpoint: {endpoint}\n")
    
    response = requests.post(endpoint, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Raw response:\n{response.text[:500]}\n")
    
    # Parse
    lines = response.text.strip().split('\n')
    content_parts = []
    for i, line in enumerate(lines):
        print(f"Line {i}: {line[:100]}")
        if line.strip():
            try:
                data = json.loads(line)
                print(f"  Parsed: {json.dumps(data, indent=2)[:200]}")
                if 'candidates' in data:
                    for candidate in data['candidates']:
                        if 'content' in candidate and 'parts' in candidate['content']:
                            for part in candidate['content']['parts']:
                                if 'text' in part:
                                    content_parts.append(part['text'])
            except Exception as e:
                print(f"  Parse error: {e}")
    
    final = ''.join(content_parts)
    print(f"\nFinal content: '{final}'")

if __name__ == "__main__":
    test_gemini_response()
