import asyncio
import time
from app.services.llm_client import get_llm_client

async def test_load():
    client = get_llm_client()
    tasks = []
    print("Simulating 10 concurrent calls to Gemini...")
    for i in range(10):
        tasks.append(client.call_llm(
            model_key="gemini-flash",
            system_prompt="You are a helpful assistant.",
            user_prompt=f"Say hello and count to {i}",
            response_format="text"
        ))
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    print(f"Completed in {end_time - start_time:.2f} seconds")
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"Call {i} FAILED: {res}")
        else:
            print(f"Call {i} SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_load())
