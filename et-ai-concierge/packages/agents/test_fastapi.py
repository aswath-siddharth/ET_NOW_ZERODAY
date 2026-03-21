import httpx
import uuid
from jose import jwt
from config import settings

def test():
    # Create valid mock token using the backend's secret
    if not settings.AUTH_SECRET:
        settings.AUTH_SECRET = "fallback_secret_for_testing"
        
    token = jwt.encode(
        {"sub": "123", "email": "test@test.com", "name": "Tester"}, 
        settings.AUTH_SECRET, 
        algorithm="HS256"
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    body = {
        "user_id": "123",
        "session_id": str(uuid.uuid4()),
        "message": "what is SIP?",
        "modality": "web"
    }
    
    target_url = "http://localhost:8000/api/chat"
    
    print(f"Sending POST to {target_url}...")
    res = httpx.post(target_url, headers=headers, json=body, timeout=60.0)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    test()
