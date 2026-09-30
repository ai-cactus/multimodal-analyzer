"""
Test different Gemini models to find which ones are available and working
"""
import asyncio
import requests
import subprocess
import json


def get_gcloud_token():
    """Get GCP access token"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting token: {e}")
        return None


async def test_gemini_model(model_name: str, project_id: str = "multimodal-analyzer", region: str = "us-central1"):
    """Test a specific Gemini model"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Region: {region}")
    print(f"{'='*60}")
    
    try:
        endpoint = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/publishers/google/models/{model_name}:generateContent"
        
        token = get_gcloud_token()
        if not token:
            print("❌ Failed to get auth token")
            return False, "No auth token"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": "Say 'Hello' and nothing else"}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 50
            }
        }
        
        print("Sending request...")
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            print(f"✅ SUCCESS!")
            print(f"Response: {text}")
            return True, text
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return False, str(e)


async def main():
    """Test multiple Gemini models"""
    print("\n🔍 Gemini Model Availability Test\n")
    
    # List of Gemini models to test (most likely to work first)
    models_to_test = [
        "gemini-1.5-pro-002",      # Latest stable Pro
        "gemini-1.5-flash-002",    # Latest stable Flash
        "gemini-1.5-pro",          # Standard Pro
        "gemini-1.5-flash",        # Standard Flash
        "gemini-2.0-flash-exp",    # Experimental 2.0
        "gemini-1.0-pro",          # Legacy Pro
        "gemini-pro",              # Alias for latest Pro
        "gemini-flash",            # Alias for latest Flash
    ]
    
    results = {}
    
    for model in models_to_test:
        success, response = await test_gemini_model(model)
        results[model] = success
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    working = []
    failed = []
    
    for model, success in results.items():
        if success:
            print(f"✅ {model}")
            working.append(model)
        else:
            print(f"❌ {model}")
            failed.append(model)
    
    if working:
        print(f"\n✅ {len(working)} model(s) working!")
        print(f"\n🎯 RECOMMENDED for RAG:")
        if "gemini-1.5-pro-002" in working:
            print("   → gemini-1.5-pro-002 (Best quality, slower)")
        elif "gemini-1.5-pro" in working:
            print("   → gemini-1.5-pro (Good quality)")
        
        if "gemini-1.5-flash-002" in working:
            print("   → gemini-1.5-flash-002 (Fast, good quality)")
        elif "gemini-1.5-flash" in working:
            print("   → gemini-1.5-flash (Fast)")
    else:
        print("\n❌ No models working. Check GCP project and API enablement.")
    
    return 0 if working else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
