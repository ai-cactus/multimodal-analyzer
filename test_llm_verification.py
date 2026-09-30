#!/usr/bin/env python3
"""
Test script to verify LLM client model verification
"""
import asyncio
import sys
import os

# Set up environment
os.environ.setdefault("GCP_PROJECT_ID", "multimodal-analyzer")
os.environ.setdefault("GCP_LOCATION", "us-east5")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/home/oluwaseyi/doc-analyzer-key.json")

# Import after env setup
from app.services.llm_client import get_llm_client

async def test_verification():
    print("=" * 60)
    print("Testing LLM Client Model Verification")
    print("=" * 60)
    
    client = get_llm_client()
    print("\nRunning model verification...")
    
    verified = await client.verify_models()
    
    print(f"\n✅ Verified models: {verified}")
    print(f"Total verified: {len(verified)} models")
    
    # Check specific models
    if 'gpt-oss' in verified:
        print("✅ gpt-oss verified successfully")
    else:
        print("❌ gpt-oss NOT verified")
        return False
    
    if 'llama-scout' in verified:
        print("✅ llama-scout verified successfully")
    else:
        print("⚠️  llama-scout NOT verified")
    
    if 'gemini-flash' in verified:
        print("✅ gemini-flash verified successfully")
    else:
        print("⚠️  gemini-flash NOT verified")
    
    if len(verified) >= 2:
        print(f"\n✅ SUCCESS: {len(verified)} models verified")
        return True
    else:
        print(f"\n❌ FAILED: Only {len(verified)} model(s) verified")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_verification())
    sys.exit(0 if success else 1)
