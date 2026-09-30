import asyncio
import json
from openai import OpenAI
import google.auth
import google.auth.transport.requests

def get_token():
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)
    return credentials.token

async def test_gpt_oss_central():
    project_id = "multimodal-analyzer"
    region = "us-central1"
    model_name = "openai/gpt-oss-120b-maas"
    
    endpoint = f"https://{region}-aiplatform.googleapis.com"
    base_url = f"{endpoint}/v1/projects/{project_id}/locations/{region}/endpoints/openapi"
    
    client = OpenAI(
        base_url=base_url,
        api_key=get_token()
    )
    
    print(f"Testing {model_name} in {region}...")
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10
        )
        print("✅ SUCCESS")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ FAILED in {region}: {e}")

if __name__ == "__main__":
    asyncio.run(test_gpt_oss_central())
