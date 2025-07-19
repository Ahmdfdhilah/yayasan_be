"""UserRole schemas for API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from src.models.enums import UserRole as UserRoleEnum
from src.schemas.shared import BaseListResponse
from typing import Optional
from datetime import date
from pydantic import Field


# ===== BASE SCHEMAS =====

class UserRoleBase(BaseModel):
    """Base user role schema."""
    user_id: int = Field(..., description="User ID")
    role_name: str = Field(..., min_length=1, max_length=50, description="Role name")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Role permissions as JSON")
    organization_id: Optional[int] = Field(None, description="Organization ID (if role is organization-specific)")
    is_active: bool = Field(default=True, description="Whether role is active")
    expires_at: Optional[datetime] = Field(None, description="Role expiration date")
    
    @field_validator('role_name')
    @classmethod
    def validate_role_name(cls, role_name: str) -> str:
        """Validate and normalize role name."""
        return role_name.strip().lower()


# ===== REQUEST SCHEMAS =====

class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role."""
    pass


class UserRoleUpdate(BaseModel):
    """Schema for updating a user role."""
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class UserRoleBulkAssign(BaseModel):
    """Schema for bulk role assignment."""
    user_ids: List[int] = Field(..., min_items=1, description="List of user IDs")
    role_name: str = Field(..., min_length=1, max_length=50)
    permissions: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = None
    expires_at: Optional[datetime] = None


# ===== RESPONSE SCHEMAS =====

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
    
    # Related data
    user_email: Optional[str] = Field(None, description="User email")
    user_name: Optional[str] = Field(None, description="User display name")
    organization_name: Optional[str] = Field(None, description="Organization name")
    
    @classmethod
    def from_user_role_model(cls, user_role, include_relations: bool = False) -> "UserRoleResponse":
        """Create UserRoleResponse from UserRole model."""
        data = {
            "id": user_role.id,
            "user_id": user_role.user_id,
            "role_name": user_role.role_name,
            "permissions": user_role.permissions,
            "organization_id": user_role.organization_id,
            "is_active": user_role.is_active,
            "expires_at": user_role.expires_at,
            "created_at": user_role.created_at,
            "updated_at": user_role.updated_at
        }
        
        if include_relations:
            data.update({
                "user_email": user_role.user.email if hasattr(user_role, 'user') and user_role.user else None,
                "user_name": user_role.user.display_name if hasattr(user_role, 'user') and user_role.user else None,
                "organization_name": user_role.organization.name if hasattr(user_role, 'organization') and user_role.organization else None
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class UserRoleListResponse(BaseListResponse[UserRoleResponse]):
    """Standardized user role list response."""
    pass


class UserRoleSummary(BaseModel):
    """Schema for user role summary (lighter response)."""
    id: int
    user_id: int
    role_name: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    # Related data
    user_email: Optional[str] = None
    organization_name: Optional[str] = None
    
    @classmethod
    def from_user_role_model(cls, user_role) -> "UserRoleSummary":
        """Create UserRoleSummary from UserRole model."""
        return cls(
            id=user_role.id,
            user_id=user_role.user_id,
            role_name=user_role.role_name,
            is_active=user_role.is_active,
            expires_at=user_role.expires_at,
            created_at=user_role.created_at,
            user_email=user_role.user.email if hasattr(user_role, 'user') and user_role.user else None,
            organization_name=user_role.organization.name if hasattr(user_role, 'organization') and user_role.organization else None
        )
    
    model_config = {"from_attributes": True}


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


# ===== FILTER SCHEMAS =====

class UserRoleFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for user role listing."""
    
    # Role-specific filters
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    role_name: Optional[str] = Field(None, description="Filter by role name")
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_permissions: Optional[bool] = Field(None, description="Filter roles with/without permissions")
    expires_soon: Optional[int] = Field(None, ge=1, le=365, description="Filter roles expiring within N days")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in role name, user email, or organization name")
    
    # Override default sort
    sort_by: str = Field(default="created_at", description="Sort field")


# ===== PERMISSION MANAGEMENT =====

class PermissionUpdate(BaseModel):
    """Schema for updating specific permissions."""
    permissions: Dict[str, Any] = Field(..., description="Permission key-value pairs")


class RolePermissionTemplate(BaseModel):
    """Schema for role permission templates."""
    role_name: str = Field(..., description="Role name")
    description: str = Field(..., description="Role description")
    permissions: Dict[str, Any] = Field(..., description="Default permissions for this role")
    is_system_role: bool = Field(default=False, description="Whether this is a system-defined role")


# ===== BULK OPERATIONS =====

class UserRoleBulkUpdate(BaseModel):
    """Schema for bulk user role updates."""
    role_ids: List[int] = Field(..., min_items=1, description="List of role IDs to update")
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class UserRoleBulkDelete(BaseModel):
    """Schema for bulk user role deletion."""
    role_ids: List[int] = Field(..., min_items=1, description="List of role IDs to delete")
    force_delete: bool = Field(default=False, description="Force delete even if role has dependencies")


# ===== ANALYTICS SCHEMAS =====

class RoleAnalytics(BaseModel):
    """Schema for role analytics."""
    role_name: str
    total_users: int
    active_users: int
    inactive_users: int
    users_by_organization: Dict[str, int] = Field(default_factory=dict)
    expiring_soon_count: int = Field(default=0, description="Roles expiring within 30 days")


class RoleAnalyticsResponse(BaseModel):
    """Schema for role analytics response."""
    summary: Dict[str, int] = Field(description="Overall role statistics")
    by_role: List[RoleAnalytics] = Field(description="Statistics per role")
    by_organization: Dict[str, Dict[str, int]] = Field(description="Statistics per organization")
    recent_assignments: int = Field(description="Role assignments in last 7 days")
    recent_revocations: int = Field(description="Role revocations in last 7 days")