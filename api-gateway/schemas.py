from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    password: str
    password2: str
    name: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh: str

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    refresh: str
    access: str

class LoginResponse(BaseModel):
    message: str
    user: UserProfileResponse
    tokens: TokenResponse

class RegistrationResponse(BaseModel):
    message: str
    user: UserProfileResponse
    tokens: TokenResponse
