"""Test Model Garden integration with actual APIs"""
import asyncio
from app.services.llm_client import get_llm_client

async def test_model_garden():
    print("=== Testing Model Garden Integration ===\n")
    
    client = get_llm_client()
    print(f"Registered models: {list(client.clients.keys())}\n")
    
    # Verify models
    print("Running pre-flight verification...")
    verified = await client.verify_models()
    print(f"✅ Verified models: {verified}\n")
    
    if not verified:
        print("❌ No models verified. Check authentication and enablement.")
        return False
    
    # Test a single model call
    print(f"Testing {verified[0]}...")
    try:
        result = await client.call_llm(
            model_key=verified[0],
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello from Model Garden!' and nothing else",
            response_format="text"
        )
        print(f"✅ SUCCESS: {result.get('response', 'N/A')[:100]}\n")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_model_garden())
    if success:
        print("✅ Model Garden integration working!")
    else:
        print("❌ Model Garden integration failed")
