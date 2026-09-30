"""Debug Claude Opus 4.5 specifically"""
from anthropic import AnthropicVertex
from app.config import get_settings
import traceback

def test_claude_detailed():
    settings = get_settings()
    
    print("=== Claude Opus 4.5 Detailed Test ===")
    print(f"Project ID: {settings.gcp_project_id}")
    print(f"Claude Region: {settings.claude_region}")
    print(f"Model: claude-opus-4-5@20251101\n")
    
    # Test 1: SDK initialization
    print("Test 1: Initializing AnthropicVertex client...")
    try:
        client = AnthropicVertex(
            region=settings.claude_region,
            project_id=settings.gcp_project_id
        )
        print("✅ Client initialized successfully\n")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}\n")
        traceback.print_exc()
        return False
    
    # Test 2: Simple message
    print("Test 2: Sending minimal message...")
    try:
        response = client.messages.create(
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": "Say 'Hello from Claude Opus!' and nothing else"
            }],
            model="claude-opus-4-5@20251101"
        )
        print(f"✅ SUCCESS!")
        print(f"Response: {response.content[0].text}\n")
        return True
    except Exception as e:
        print(f"❌ Message creation failed")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}\n")
        print("Full traceback:")
        traceback.print_exc()
        
        # Check specific error types
        if "403" in str(e):
            print("\n💡 403 Forbidden - Possible causes:")
            print("   - Claude not enabled in your GCP project")
            print("   - Missing permissions")
        elif "404" in str(e):
            print("\n💡 404 Not Found - Possible causes:")
            print("   - Wrong region (try 'us-east5' instead of 'global')")
            print("   - Model not available in this region")
        elif "401" in str(e):
            print("\n💡 401 Unauthorized - Possible causes:")
            print("   - Authentication issue")
            print("   - Run: gcloud auth application-default login")
        
        return False

if __name__ == "__main__":
    success = test_claude_detailed()
    
    if not success:
        print("\n" + "="*60)
        print("TROUBLESHOOTING STEPS:")
        print("="*60)
        print("\n1. Verify Claude is enabled in Model Garden:")
        print("   https://console.cloud.google.com/vertex-ai/publishers/anthropic/model-garden/claude-opus-4-5?project=multimodal-analyzer")
        print("\n2. Try different regions in .env:")
        print("   CLAUDE_REGION=us-east5")
        print("   CLAUDE_REGION=europe-west1")
        print("\n3. Check authentication:")
        print("   gcloud auth application-default login")
        print("   gcloud auth application-default print-access-token")
