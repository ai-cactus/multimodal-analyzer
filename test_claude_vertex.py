"""Test Vertex AI Model Garden with Claude"""
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage
from app.config import get_settings

def test_claude_vertex():
    settings = get_settings()
    print(f"Project: {settings.gcp_project_id}")
    print(f"Location: {settings.gcp_location}")
    
    print("\n=== Testing Claude 3.5 Sonnet via Model Garden ===")
    
    try:
        model = ChatVertexAI(
            model_name="claude-3-5-sonnet@20240620",
            project=settings.gcp_project_id,
            location=settings.gcp_location,
            max_retries=1
        )
        print("✓ Model initialized")
        
        response = model.invoke([HumanMessage(content="Say 'Hello from Claude!' and nothing else")])
        print(f"✅ SUCCESS: {response.content}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"Details: {str(e)[:300]}")
        
        if "404" in str(e):
            print("\n💡 Possible issues:")
            print("1. Claude not enabled in Model Garden")
            print("   → Visit: https://console.cloud.google.com/vertex-ai/publishers/anthropic/model-garden/claude-3-5-sonnet")
            print("   → Click 'Enable' if needed")
            print("2. Wrong region - try 'us-east5' or 'europe-west1'")
        elif "403" in str(e) or "PERMISSION_DENIED" in str(e):
            print("\n💡 Permission issue:")
            print("   Run: gcloud auth application-default login")
        
        return False

if __name__ == "__main__":
    success = test_claude_vertex()
    if not success:
        print("\n=== Alternative: Check available models ===")
        print("Run: gcloud ai models list --region=us-central1")
