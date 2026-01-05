from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from jose import jwt, JWTError
from typing import Optional
import redis
import time
from datetime import datetime, timezone
from schemas import (
    UserRegistration, UserLogin, TokenRefresh, UserProfileUpdate,
    RegistrationResponse, LoginResponse
)

app = FastAPI(
    title="Smart Expense Tracker - API Gateway",
    description="API Gateway for microservices-based expense tracker",
    version="1.0.0"
)

# CORS middleware conf
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
EXPENSE_SERVICE_URL = os.getenv("EXPENSE_SERVICE_URL", "http://expense-service:8002")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8003")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8004")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
    print("Connected to Redis!")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None


# Rate limiting
async def rate_limit(request: Request):
    """Simple rate limiting: 100 requests per minute per IP"""
    if redis_client is None:
        return # skip reate limiting if redis is not available
    
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        current = redis_client.get(key)
        if current is None:
            redis_client.setex(key, 60, 1)
        else:
            if int(current) >= 100:
                raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
            redis_client.incr(key)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Rate limiting error: {e}")


# JWT token validation
def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_token_from_header(request: Request) -> Optional[str]:
    """Extract token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None

@app.get("/")
async def root():
    """Gateway health check"""
    return {
        "service": "API Gateway",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "auth_service": AUTH_SERVICE_URL,
            "expense_service": EXPENSE_SERVICE_URL,
            "analytics_service": ANALYTICS_SERVICE_URL,
            "notification_service": NOTIFICATION_SERVICE_URL
        }
    }

@app.get("/health")
async def health_check():
    """Check health of all services"""
    services_health = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/health")
            services_health["auth_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_health["auth_service"] = "unreachable"
        
        try:
            response = await client.get(f"{EXPENSE_SERVICE_URL}/health")
            services_health["expense_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_health["expense_service"] = "unreachable"
        
        try:
            response = await client.get(f"{ANALYTICS_SERVICE_URL}/health")
            services_health["analytics_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_health["analytics_service"] = "unreachable"
        
        try:
            response = await client.get(f"{NOTIFICATION_SERVICE_URL}/health")
            services_health["notification_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_health["notification_service"] = "unreachable"
    
    return {
        "gateway": "healthy",
        "services": services_health,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Auth-service routes
@app.post("/api/auth/register", response_model=RegistrationResponse)
async def register_user(user_data: UserRegistration, request: Request):
    """Forward registration request to User Service"""
    await rate_limit(request)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/api/auth/register", json=user_data.dict())
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")


@app.post("/api/auth/login", response_model=LoginResponse)
async def login_user(user_data: UserLogin, request: Request):
    """Forward login request to User Service"""
    await rate_limit(request)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/api/auth/login", json=user_data.dict())
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")


@app.post("/api/auth/refresh")
async def refresh_token(token_data: TokenRefresh, request: Request):
    """Forward token refresh request to User Service"""
    await rate_limit(request)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/api/auth/refresh", json=token_data.dict())
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")


@app.get("/api/users/profile")
async def get_user_profile(request: Request):
    """Forward get profile request to User Service"""
    await rate_limit(request)
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    verify_token(token)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/users/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")


@app.put("/api/users/profile")
async def update_user_profile(profile_data: UserProfileUpdate, request: Request):
    """Forward update profile request to User Service"""
    await rate_limit(request)
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    verify_token(token)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.put(
                f"{AUTH_SERVICE_URL}/api/users/profile",
                json=profile_data.dict(exclude_unset=True),
                headers={"Authorization": f"Bearer {token}"}
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"User service unavailable: {str(e)}")



# Expense-service routes
async def forward_to_expense_service(request: Request, path: str = ""):
    """Helper function to forward requests to Expense Service"""
    await rate_limit(request)
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    payload = verify_token(token) 
    
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.json()
    
    # Build URL with query parameters
    url = f"{EXPENSE_SERVICE_URL}/api/expenses"
    if path:
        url += f"/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    print("url is: ", url)
    print("token is: ", token)
    print("payload is: ", payload)
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-User-ID": str(payload.get("user_id", ""))
                }
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Expense service unavailable: {str(e)}")


@app.api_route("/api/expenses", methods=["GET", "POST", "PUT", "DELETE"])
async def expense_service_proxy_base(request: Request):
    """Forward requests to /api/expenses (base endpoint)"""
    print("forwarding request to /api/expenses.........")
    return await forward_to_expense_service(request, "")


@app.api_route("/api/expenses/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def expense_service_proxy(request: Request, path: str):
    """Forward all expense-related requests to Expense Service"""
    return await forward_to_expense_service(request, path)


# Analytics-service routes
@app.api_route("/api/analytics/{path:path}", methods=["GET", "POST", "PUT"])
async def analytics_service_proxy(request: Request, path: str):
    """Forward all analytics-related requests to Analytics Service"""
    await rate_limit(request)
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    payload = verify_token(token) 
    
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.json()
    
    # Build URL with query parameters
    url = f"{ANALYTICS_SERVICE_URL}/api/analytics"
    if path:
        url += f"/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-User-ID": str(payload.get("user_id", ""))
                }
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Analytics service unavailable: {str(e)}")


# Notification-service routes
@app.api_route("/api/notifications/{path:path}", methods=["GET", "POST", "PUT"])
async def notification_service_proxy(request: Request, path: str):
    """Forward all notification-related requests to Notification Service"""
    await rate_limit(request)
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    payload = verify_token(token)  
    
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.json()
    
    # Build URL with query parameters
    url = f"{NOTIFICATION_SERVICE_URL}/api/notifications"
    if path:
        url += f"/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-User-ID": str(payload.get("user_id", ""))
                }
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Notification service unavailable: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
