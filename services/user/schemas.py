"""Pydantic schemas for User Service."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class RoleBase(BaseModel):
    """Base role schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)


# Request schemas
class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, max_length=128)
    role_id: UUID


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    role_id: Optional[UUID] = None
    active: Optional[bool] = None


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class RoleCreate(RoleBase):
    """Schema for creating a role."""


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None


class PasswordChange(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# Response schemas
class RoleResponse(RoleBase):
    """Schema for role response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    active: bool
    role: RoleResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    """Schema for message response."""

    message: str


# Internal schemas
class TokenData(BaseModel):
    """Schema for token data."""

    user_id: Optional[UUID] = None
    username: Optional[str] = None
    role_id: Optional[UUID] = None
    permissions: Optional[Dict[str, Any]] = None
