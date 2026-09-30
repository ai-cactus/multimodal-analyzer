"""
Test Llama Scout using the actual llm_client implementation
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/home/oluwaseyi/dev247/official/multimodal-analyzer')

from app.services.llm_client import get_llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_llama_scout():
    """Test Llama Scout connectivity with actual implementation"""
    print("=" * 60)
    print("Testing Llama Scout Configuration")
    print("=" * 60)
    
    try:
        # Get the LLM client
        client = get_llm_client()
        
        print("\n1. Registered models:")
        for model_key in client.clients.keys():
            print(f"   - {model_key}")
        
        # Verify llama-scout is registered
        if "llama-scout" not in client.clients:
            print("\n❌ ERROR: llama-scout not found in registered clients!")
            return False
        
        print("\n2. Testing llama-scout connectivity...")
        
        # Attempt a simple call
        result = await client.call_llm(
            model_key="llama-scout",
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello World!' and nothing else.",
            response_format="text"
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Response: {result.get('response', '')[:200]}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        logger.error(f"Llama Scout test failed", exc_info=True)
        return False


async def test_gpt_oss():
    """Test GPT-OSS if configured"""
    print("\n" + "=" * 60)
    print("Testing GPT-OSS Configuration")
    print("=" * 60)
    
    try:
        client = get_llm_client()
        
        if "gpt-oss" not in client.clients:
            print("\n⚠️  GPT-OSS not yet configured (expected)")
            return None
        
        print("\n2. Testing gpt-oss connectivity...")
        
        result = await client.call_llm(
            model_key="gpt-oss",
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello World!' and nothing else.",
            response_format="text"
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Response: {result.get('response', '')[:200]}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        logger.error(f"GPT-OSS test failed", exc_info=True)
        return False


async def main():
    print("\nMulti-LLM Configuration Test\n")
    
    # Test Llama Scout
    llama_success = await test_llama_scout()
    
    # Test GPT-OSS
    gpt_success = await test_gpt_oss()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if llama_success:
        print("✅ Llama Scout: Working")
    else:
        print("❌ Llama Scout: Failed")
    
    if gpt_success is True:
        print("✅ GPT-OSS: Working")
    elif gpt_success is False:
        print("❌ GPT-OSS: Failed")
    else:
        print("⚠️  GPT-OSS: Not configured yet")
    
    if llama_success:
        print("\n✅ At least one model is working! System is ready.")
        return 0
    else:
        print("\n❌ No models are working. Please check configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
