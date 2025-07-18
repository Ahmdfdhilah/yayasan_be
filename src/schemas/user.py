"""Updated user schemas for unified schema."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field
from datetime import datetime

from src.models.enums import UserStatus
from src.schemas.shared import BaseListResponse, MessageResponse


# ===== BASE SCHEMAS =====

class UserBase(BaseModel):
    """Base user schema with unified fields."""
    email: EmailStr = Field(..., description="User email address")
    profile: Dict[str, Any] = Field(..., description="User profile data as JSON")
    organization_id: Optional[int] = Field(None, description="Organization ID")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="User status")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and normalize email."""
        return email.lower().strip()
    
    @field_validator('profile')
    @classmethod
    def validate_profile(cls, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile has required fields."""
        if not profile.get('name'):
            raise ValueError("Profile must contain 'name' field")
        return profile


# ===== REQUEST SCHEMAS =====

class UserCreate(UserBase):
    """Schema for creating a user."""
    password: Optional[str] = Field(None, min_length=6, max_length=128, description="Optional password, uses default if not provided")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    profile: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = None
    status: Optional[UserStatus] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, email: Optional[str]) -> Optional[str]:
        """Validate and normalize email if provided."""
        return email.lower().strip() if email else None


class UserChangePassword(BaseModel):
    """Schema for changing password."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)


# ===== RESPONSE SCHEMAS =====

class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    profile: Dict[str, Any]
    organization_id: Optional[int] = None
    status: UserStatus
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    display_name: str = Field(..., description="Display name from profile")
    full_name: str = Field(..., description="Full name from profile")
    roles: List[str] = Field(default_factory=list, description="User roles")
    
    @classmethod
    def from_user_model(cls, user) -> "UserResponse":
        """Create UserResponse from User model."""
        return cls(
            id=user.id,
            email=user.email,
            profile=user.profile or {},
            organization_id=user.organization_id,
            status=user.status,
            email_verified_at=user.email_verified_at,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            display_name=user.display_name,
            full_name=user.full_name,
            roles=user.get_roles() if hasattr(user, 'get_roles') else []
        )
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseListResponse[UserResponse]):
    """Standardized user list response."""
    pass


class UserSummary(BaseModel):
    """Schema for user summary (lighter response)."""
    id: int
    email: str
    display_name: str
    organization_id: Optional[int] = None
    status: UserStatus
    roles: List[str] = Field(default_factory=list)
    is_active: bool
    last_login_at: Optional[datetime] = None
    
    @classmethod
    def from_user_model(cls, user) -> "UserSummary":
        """Create UserSummary from User model."""
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            organization_id=user.organization_id,
            status=user.status,
            roles=user.get_roles() if hasattr(user, 'get_roles') else [],
            is_active=user.is_active(),
            last_login_at=user.last_login_at
        )
    
    model_config = ConfigDict(from_attributes=True)


# ===== AUTH SCHEMAS =====

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="Email for login")
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserResponse


class TokenRefresh(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=6, max_length=128)


# ===== ROLE MANAGEMENT SCHEMAS =====

class UserRoleCreate(BaseModel):
    """Schema for creating user role."""
    user_id: int
    role_name: str = Field(..., min_length=1, max_length=50)
    permissions: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role."""
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class UserRoleResponse(BaseModel):
    """Schema for user role response."""
    id: int
    user_id: int
    role_name: str
    permissions: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ===== LEGACY COMPATIBILITY SCHEMAS =====

class PerwadagSummary(UserSummary):
    """Legacy schema for perwadag summary."""
    inspektorat: Optional[str] = None
    
    @classmethod
    def from_user_model(cls, user) -> "PerwadagSummary":
        """Create PerwadagSummary from User model."""
        base = super().from_user_model(user)
        return cls(
            **base.model_dump(),
            inspektorat=user.get_profile_field('inspektorat') if hasattr(user, 'get_profile_field') else None
        )


class PerwadagListResponse(BaseListResponse[PerwadagSummary]):
    """Legacy response for perwadag list."""
    pass