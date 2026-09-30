"""
Test the updated llm_client configuration with priority on llama-scout
"""
import asyncio
import sys
sys.path.insert(0, '/home/oluwaseyi/dev247/official/multimodal-analyzer')

from app.services.llm_client import get_llm_client


async def test_updated_config():
    print("=" * 60)
    print("Testing Updated LLM Client Configuration")
    print("=" * 60)
    
    client = get_llm_client()
    
    print("\n1. Registered models:")
    for model_key in client.clients.keys():
        print(f"   - {model_key}")
    
    print("\n2. Verifying models...")
    verified = await client.verify_models()
    
    print(f"\n3. Verified models ({len(verified)}):")
    for model in verified:
        print(f"   ✅ {model}")
    
    print("\n4. Testing llama-scout call...")
    try:
        result = await client.call_llm(
            model_key="llama-scout",
            system_prompt="You are a compliance analyst.",
            user_prompt="What is your role? Answer in one sentence.",
            response_format="text"
        )
        print(f"   ✅ Success: {result.get('response', '')[:100]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n5. Testing multi-model call...")
    try:
        results = await client.call_multi_llm(
            models=verified,
            system_prompt="You are helpful.",
            user_prompt="Say 'test' and nothing else.",
            response_format="text"
        )
        print(f"   ✅ Got responses from {len(results)} models")
        for model, response in results.items():
            if 'error' not in response:
                print(f"      - {model}: {str(response.get('response', ''))[:50]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! System ready for analysis.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_updated_config())
    sys.exit(0 if success else 1)
