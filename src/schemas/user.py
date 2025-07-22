"""Updated user schemas for unified schema."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field
from datetime import datetime, date

from src.models.enums import UserStatus, UserRole
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
    """Schema for updating a user (self-update, no email)."""
    profile: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = None
    status: Optional[UserStatus] = None


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user (includes email)."""
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
    organization_name: Optional[str] = Field(None, description="Organization name")
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    display_name: str = Field(..., description="Display name from profile")
    full_name: str = Field(..., description="Full name from profile")
    roles: List[str] = Field(default_factory=list, description="User roles")
    
    @classmethod
    def from_user_model(cls, user, roles: List[str] = None) -> "UserResponse":
        """Create UserResponse from User model."""
        organization_name = None
        # Check if organization is loaded and avoid lazy loading
        try:
            if hasattr(user, '__dict__') and 'organization' in user.__dict__ and user.organization:
                organization_name = user.organization.name
        except:
            # If there's any issue accessing organization, keep it as None
            pass
        
        return cls(
            id=user.id,
            email=user.email,
            profile=user.profile or {},
            organization_id=user.organization_id,
            organization_name=organization_name,
            status=user.status,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            display_name=user.display_name,
            full_name=user.full_name,
            roles=roles or []
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


# ===== BASE FILTER SCHEMAS =====

class PaginationParams(BaseModel):
    """Base pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")


class SearchParams(BaseModel):
    """Base search parameters."""
    
    q: Optional[str] = Field(default=None, description="Search query")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class DateRangeFilter(BaseModel):
    """Date range filter parameters."""
    
    start_date: Optional[date] = Field(default=None, description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date")


# ===== USER FILTER SCHEMAS =====

class UserFilterParams(BaseModel):
    """Filter parameters for user listing."""
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Search and filtering
    search: Optional[str] = Field(default=None, description="Search in name, email, or username")
    role: Optional[UserRole] = Field(default=None, description="Filter by user role")
    status: Optional[UserStatus] = Field(default=None, description="Filter by user status")
    organization_id: Optional[int] = Field(default=None, description="Filter by organization")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    
    # Date filtering
    created_after: Optional[date] = Field(default=None, description="Filter users created after this date")
    created_before: Optional[date] = Field(default=None, description="Filter users created before this date")
    
    # Active/inactive filter
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")


class UsernameGenerationPreview(BaseModel):
    """Preview data for username generation."""
    
    nama: str = Field(..., min_length=1, max_length=200)
    role: UserRole = Field(...)
    organization_name: Optional[str] = Field(default=None, max_length=100)


class UsernameGenerationResponse(BaseModel):
    """Response for username generation preview."""
    
    original_nama: str
    organization_name: Optional[str]
    role: UserRole
    generated_username: str
    is_available: bool
    suggested_alternatives: list[str] = Field(default_factory=list)


