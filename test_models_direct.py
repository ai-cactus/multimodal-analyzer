"""
Simple test of llm_client directly without importing the full app
"""
import asyncio
import sys
import os

# Set up environment first
os.environ.setdefault("GCP_PROJECT_ID", "multimodal-analyzer")
os.environ.setdefault("GCP_LOCATION", "us-east5")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/home/oluwaseyi/doc-analyzer-key.json")
os.environ.setdefault("CLAUDE_REGION", "global")
os.environ.setdefault("LLAMA_REGION", "us-east5")
os.environ.setdefault("GEMINI_REGION", "global")

# Import just what we need
from anthropic import AnthropicVertex
from openai import OpenAI
import requests
import json
import google.auth
import google.auth.transport.requests


def get_gcloud_token():
    """Get GCP access token"""
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        return credentials.token
    except Exception as e:
        print(f"Error getting token: {e}")
        return None


async def test_llama_scout():
    """Test Llama Scout directly"""
    print("=" * 60)
    print("Testing Llama Scout (OpenAI-compatible endpoint)")
    print("=" * 60)
    
    try:
        project_id = "multimodal-analyzer"
        region = "us-east5"
        model_name = "meta/llama-4-scout-17b-16e-instruct-maas"
        
        endpoint = f"https://{region}-aiplatform.googleapis.com"
        base_url = f"{endpoint}/v1/projects/{project_id}/locations/{region}/endpoints/openapi"
        
        print(f"\nEndpoint: {base_url}")
        print(f"Model: {model_name}")
        
        token = get_gcloud_token()
        if not token:
            print("❌ Failed to get auth token")
            return False
        
        client = OpenAI(
            base_url=base_url,
            api_key=token,
            timeout=60.0
        )
        
        print("\nSending test request...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'Hello World!' and nothing else."}],
            max_tokens=50,
            temperature=0.1
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return False


async def test_gemini_flash():
    """Test Gemini Flash via REST API"""
    print("\n" + "=" * 60)
    print("Testing Gemini Flash (REST API)")
    print("=" * 60)
    
    try:
        project_id = "multimodal-analyzer"
        region = "us-central1"
        model_name = "gemini-2.0-flash-001"  # Gemini 2.0 Flash (latest)
        
        endpoint = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/publishers/google/models/{model_name}:generateContent"
        
        print(f"\nEndpoint: {endpoint}")
        print(f"Model: {model_name}")
        
        token = get_gcloud_token()
        if not token:
            print("❌ Failed to get auth token")
            return False
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": {
                "role": "user",
                "parts": [{"text": "Say 'Hello World!' and nothing else."}]
            },
            "generation_config": {
                "maxOutputTokens": 50,
                "temperature": 0.1
            }
        }
        
        print("\nSending test request...")
        
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract text from response - handle both streaming and non-streaming
        try:
            # Non-streaming format (Gemini 2.0)
            if 'candidates' in data:
                candidates = data['candidates']
                if candidates and len(candidates) > 0:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        text = parts[0].get('text', '')
                        print(f"\n✅ SUCCESS!")
                        print(f"Response: {text.strip()}")
                        return True
            # Streaming format (list response)
            elif isinstance(data, list) and len(data) > 0:
                candidates = data[0].get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        text = parts[0].get('text', '')
                        print(f"\n✅ SUCCESS!")
                        print(f"Response: {text.strip()}")
                        return True
        except Exception as parse_error:
            print(f"\n⚠️  Parsing error: {parse_error}")
        
        print(f"\n⚠️  Got response but couldn't parse: {data}")
        return False
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return False


async def test_claude_opus():
    """Test Claude Opus via AnthropicVertex"""
    print("\n" + "=" * 60)
    print("Testing Claude Opus (AnthropicVertex SDK)")
    print("=" * 60)
    
    try:
        project_id = "multimodal-analyzer"
        region = "global"
        model_name = "claude-opus-4-5@20251101"
        
        print(f"\nProject: {project_id}")
        print(f"Region: {region}")
        print(f"Model: {model_name}")
        
        print("\nInitializing AnthropicVertex client...")
        client = AnthropicVertex(
            region=region,
            project_id=project_id
        )
        
        print("Sending test request...")
        
        response = client.messages.create(
            max_tokens=50,
            temperature=0.1,
            messages=[{"role": "user", "content": "Say 'Hello World!' and nothing else."}],
            model=model_name
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Response: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return False


async def test_gpt_oss():
    """Test GPT-OSS via OpenAI-compatible endpoint"""
    print("\n" + "=" * 60)
    print("Testing GPT-OSS (OpenAI-compatible endpoint)")
    print("=" * 60)
    
    try:
        project_id = "multimodal-analyzer"
        region = "global"
        model_name = "openai/gpt-oss-120b-maas"
        
        endpoint = f"https://aiplatform.googleapis.com"
        base_url = f"{endpoint}/v1/projects/{project_id}/locations/{region}/endpoints/openapi"
        
        print(f"\nEndpoint: {base_url}")
        print(f"Model: {model_name}")
        
        token = get_gcloud_token()
        if not token:
            print("❌ Failed to get auth token")
            return False
        
        client = OpenAI(
            base_url=base_url,
            api_key=token,
            timeout=60.0
        )
        
        print("\nSending test request...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'Hello World!' and nothing else"}],
            max_tokens=50,
            temperature=0.1
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return False


async def main():
    print("\n🔍 Multi-LLM Direct Connection Test\n")
    
    results = {}
    
    # Test each model
    results['llama-scout'] = await test_llama_scout()
    results['gemini-flash'] = await test_gemini_flash()
    results['claude-opus'] = await test_claude_opus()
    results['gpt-oss'] = await test_gpt_oss()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for model, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{status}: {model}")
    
    working_count = sum(1 for success in results.values() if success)
    
    if working_count > 0:
        print(f"\n✅ {working_count} model(s) working! System is ready.")
        return 0
    else:
        print("\n❌ No models are working. Need to fix configurations.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
