# Pydantic schemas for User module
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    nama: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role_id: Optional[int] = 2  # default to 'user'

class UserUpdate(BaseModel):
    nama: Optional[str] = Field(None, max_length=100)
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    nrp: str
    nama: str
    email: str
    role_id: int
    role_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Auth schemas
class LoginRequest(BaseModel):
    identifier: str  # email or nrp
    password: str
    androidId: Optional[str] = None  # for device pairing

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None  # include user profile

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Role schemas
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
