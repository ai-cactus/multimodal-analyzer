"""Test a single Gemini model to diagnose the issue"""
import os
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage
from app.config import get_settings

def test_single_model():
    settings = get_settings()
    print(f"Project: {settings.gcp_project_id}")
    print(f"Location: {settings.gcp_location}")
    
    print("\n=== Testing gemini-1.5-pro ===")
    try:
        model = ChatVertexAI(
            model_name="gemini-1.5-pro",
            project=settings.gcp_project_id,
            location=settings.gcp_location,
            max_retries=1
        )
        print("Model initialized successfully")
        
        response = model.invoke([HumanMessage(content="Say 'Hello World' and nothing else")])
        print(f"SUCCESS: {response.content}")
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:200]}")
        return False

if __name__ == "__main__":
    success = test_single_model()
    if not success:
        print("\n❌ Model verification failed. Please check:")
        print("1. Run: gcloud auth application-default login")
        print("2. Run: gcloud config set project multimodal-analyzer")
        print("3. Ensure Vertex AI API is enabled")
        print("4. Grant IAM role: gcloud projects add-iam-policy-binding multimodal-analyzer \\")
        print("     --member='user:o.sholanke@gmail.com' \\")
        print("     --role='roles/aiplatform.user'")
