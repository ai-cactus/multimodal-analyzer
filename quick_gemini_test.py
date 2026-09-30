"""
Quick test to find working Gemini configuration
"""
import requests
import subprocess


def get_token():
    result = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True)
    return result.stdout.strip()


def test_gemini(region, model):
    project = "multimodal-analyzer"
    endpoint = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/publishers/google/models/{model}:generateContent"
    
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Hello"}]
        }],
        "generationConfig": {"maxOutputTokens": 10}
    }
    
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            print(f"✅ {region:15} | {model:30} | WORKS")
            return True
        else:
            print(f"❌ {region:15} | {model:30} | {resp.status_code}")
    except Exception as e:
        print(f"❌ {region:15} | {model:30} | {str(e)[:40]}")
    return False


if __name__ == "__main__":
    print("\n Testing Gemini Models\n")
    print(f"{'Region':<15} | {'Model':<30} | Status\n" + "="*70)
    
    regions = ["us-central1", "us-east4", "europe-west1"]
    models = [
        "gemini-1.5-flash-002",
        "gemini-1.5-flash-001", 
        "gemini-1.5-flash",
        "gemini-1.5-pro-002",
        "gemini-1.5-pro-001",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp",
    ]
    
    working = []
    for region in regions:
        for model in models:
            if test_gemini(region, model):
                working.append((region, model))
    
    if working:
        print(f"\n✅ Found {len(working)} working configuration(s):")
        for r, m in working:
            print(f"   {r} → {m}")
    else:
        print("\n❌ No working Gemini configurations found")
