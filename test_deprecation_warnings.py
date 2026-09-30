#!/usr/bin/env python3
"""
Test script to check for deprecation warnings
"""
import asyncio
import sys
import os

# Set up environment
os.environ.setdefault("GCP_PROJECT_ID", "multimodal-analyzer")
os.environ.setdefault("GCP_LOCATION", "us-east5")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/home/oluwaseyi/doc-analyzer-key.json")

async def test_no_warnings():
    print("=" * 60)
    print("Testing for Deprecation Warnings")
    print("=" * 60)
    
    print("\n1. Testing embedding service...")
    from app.services.embedding import get_embedding_service
    emb_service = get_embedding_service()
    emb = await emb_service.generate_embedding('test text for embedding')
    print(f"   ✅ Embedding generated: {len(emb)} dimensions")
    
    print("\n2. Testing LLM client...")
    from app.services.llm_client import get_llm_client
    client = get_llm_client()
    verified = await client.verify_models()
    print(f"   ✅ Verified models: {verified}")
    
    print("\n3. Testing Gemini call...")
    if 'gemini-flash' in verified:
        result = await client.call_llm(
            'gemini-flash',
            'You are a helpful assistant.',
            'Say hello in one word.',
            response_format='text'
        )
        print(f"   ✅ Gemini response received")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("Check above - if you see any 'UserWarning' or 'deprecated',")
    print("then warnings are not being suppressed correctly.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_no_warnings())
