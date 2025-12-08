from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SiteBase(BaseModel):
    slug: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9-]+$")
    display_name: Optional[str] = None
    domain: Optional[str] = None
    visibility: str = "public"
    ip_whitelist: Optional[List[str]] = None

class SiteCreate(SiteBase):
    site_password: Optional[str] = None # Plain text password to be hashed in backend

class SiteUpdate(BaseModel):
    display_name: Optional[str] = None
    domain: Optional[str] = None
    visibility: Optional[str] = None
    site_password: Optional[str] = None
    ip_whitelist: Optional[List[str]] = None

class SiteOut(SiteBase):
    id: str
    owner_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: str
    role: str
    class Config:
        orm_mode = True
