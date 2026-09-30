"""Test actual enabled models from Model Garden"""
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage
from app.config import get_settings

def test_enabled_models():
    settings = get_settings()
    print(f"Project: {settings.gcp_project_id}")
    print(f"Location: {settings.gcp_location}")
    
    models_to_test = [
        ("Claude Opus 4.5", "claude-opus-4-5@20251101"),
        ("Llama 4 Maverick", "meta/llama-4-maverick-17b-128e-instruct-maas"),
        ("Llama 4 Scout", "meta/llama-4-scout-17b-16e-instruct-maas"),
    ]
    
    results = []
    for display_name, model_id in models_to_test:
        print(f"\n=== Testing {display_name} ===")
        print(f"Model ID: {model_id}")
        
        try:
            model = ChatVertexAI(
                model_name=model_id,
                project=settings.gcp_project_id,
                location=settings.gcp_location,
                max_retries=1
            )
            print("✓ Initialized")
            
            response = model.invoke([HumanMessage(content="Say 'Hello!' and nothing else")])
            print(f"✅ SUCCESS: {response.content[:100]}")
            results.append((display_name, True))
        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}")
            print(f"   {str(e)[:200]}")
            results.append((display_name, False))
    
    print("\n" + "="*50)
    print("SUMMARY:")
    for name, success in results:
        status = "✅ Working" if success else "❌ Failed"
        print(f"{status}: {name}")
    
    working_count = sum(1 for _, success in results if success)
    return working_count > 0

if __name__ == "__main__":
    success = test_enabled_models()
    if success:
        print("\n✅ At least one model is working! Ready for analysis.")
    else:
        print("\n❌ No models worked. Check authentication and region settings.")
