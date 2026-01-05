import httpx
import asyncio
import uuid

BASE_URL = "http://localhost:8000"

async def test_welcome_email():
    """Test user registration and welcome email"""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "StrongPassword@123!"
    
    print(f"🧪 Testing welcome email functionality")
    print(f"📧 Registering user: {email}")
    
    async with httpx.AsyncClient() as client:
        reg_data = {
            "email": email,
            "username": username,
            "password": password,
            "password2": password,
            "name": "Email Test User"
        }
        
        resp = await client.post(f"{BASE_URL}/api/auth/register", json=reg_data)
        
        if resp.status_code == 201:
            print(f"✅ User registered successfully!")
            print(f"\n📨 Welcome email should be sent to: {email}")
            print(f"\n🔍 Check notification service logs:")
            print(f"   docker logs notification-service --tail 30")
            print(f"\n🔍 Check auth service logs:")
            print(f"   docker logs auth-service --tail 20")
            print(f"\n💡 If using Mailtrap, check your inbox at: https://mailtrap.io")
        else:
            print(f"❌ Registration failed: {resp.status_code}")
            print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_welcome_email())
