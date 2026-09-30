import asyncio
import json
from app.services.llm_client import get_llm_client

async def test_gemini():
    client = get_llm_client()
    print("Testing gemini-flash specifically...")
    try:
        result = await client.call_llm(
            model_key="gemini-flash",
            system_prompt="You are a professional auditor.",
            user_prompt="Explain the importance of compliance in 3 bullet points.",
            response_format="text"
        )
        print("✅ SUCCESS:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
