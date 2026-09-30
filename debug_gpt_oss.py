import asyncio
import json
from app.services.llm_client import get_llm_client

async def debug_gpt_oss():
    client = get_llm_client()
    print("Testing gpt-oss probe...")
    
    # Manually trigger probe with detailed logging
    model_key = "gpt-oss"
    if model_key not in client.clients:
        print(f"Model {model_key} not in clients list (likely failed registration)")
        return

    client_info = client.clients[model_key]
    provider = client_info["provider"]
    config = client_info["config"]
    
    try:
        if provider == "llama":
            print(f"Calling OpenAI-compatible endpoint: {client_info['client'].base_url}")
            print(f"Model name: {config['model_name']}")
            
            response = client_info["client"].chat.completions.create(
                model=config["model_name"],
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print("✅ SUCCESS")
            print(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        if hasattr(e, 'response'):
             print(f"Response status: {e.response.status_code}")
             print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    asyncio.run(debug_gpt_oss())
