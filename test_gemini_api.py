"""Test Gemini API connectivity with new SDK"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def test_gemini_api():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ No GOOGLE_API_KEY found in environment")
        print("\n📝 To fix:")
        print("1. Get your API key from: https://aistudio.google.com/app/apikey")
        print("2. Add to .env: GOOGLE_API_KEY=your_actual_key")
        print("3. Restart the server")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...")
    print("\n=== Testing Gemini 2.0 Flash Experimental ===")
    
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            convert_system_message_to_human=True
        )
        
        response = model.invoke([HumanMessage(content="Say 'Hello from Gemini 2.0!' and nothing else")])
        print(f"✅ SUCCESS: {response.content}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)[:200]}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    if success:
        print("\n✅ Gemini API is working! Your analysis should now produce results.")
    else:
        print("\n❌ Please fix the API key issue and try again.")
