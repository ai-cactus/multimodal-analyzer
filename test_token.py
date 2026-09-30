"""Test the improved token generation"""
import os
import sys
from app.config import get_settings

# Explicitly load settings
settings = get_settings()

def test_token():
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    
    import google.auth
    import google.auth.transport.requests
    
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        print(f"✅ Credentials found for project: {project}")
        print(f"Account: {credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'User Account'}")
        
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        token = credentials.token
        print(f"✅ Token generated successfully: {token[:10]}...")
        return True
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        return False

if __name__ == "__main__":
    test_token()
