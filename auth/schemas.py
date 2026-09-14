from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    identifier: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthenticatedUser(BaseModel):
    id: Optional[int] = None
    username: str
    email: Optional[str] = None
    is_active: bool

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
