"""Organization schemas for API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# Remove OrganizationType import as it's no longer needed
from src.schemas.shared import BaseListResponse
from typing import Optional
from datetime import date
from pydantic import Field


# ===== BASE SCHEMAS =====

class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    excerpt: Optional[str] = Field(None, max_length=500, description="Short summary excerpt")
    img_url: Optional[str] = Field(None, max_length=500, description="Organization image URL")
    head_id: Optional[int] = Field(None, description="ID of the organization head/principal")
    display_order: int = Field(default=1, ge=1, description="Display order for sorting organizations")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate and normalize organization name."""
        return name.strip()


# ===== REQUEST SCHEMAS =====

class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=500, description="Short summary excerpt")
    img_url: Optional[str] = Field(None, max_length=500, description="Organization image URL")
    head_id: Optional[int] = Field(None, description="ID of the organization head/principal")
    display_order: Optional[int] = Field(None, ge=1, description="Display order for sorting organizations")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: Optional[str]) -> Optional[str]:
        """Validate and normalize organization name if provided."""
        return name.strip() if name else None


# ===== RESPONSE SCHEMAS =====

class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    id: int
    name: str
    description: Optional[str] = None
    excerpt: Optional[str] = None
    img_url: Optional[str] = None
    head_id: Optional[int] = None
    display_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    display_name: str = Field(..., description="Display name for organization")
    user_count: int = Field(default=0, description="Number of users in organization")
    head_name: Optional[str] = Field(None, description="Name of the organization head")
    
    @classmethod
    def from_organization_model(cls, org, user_count: int = 0, head_name: Optional[str] = None) -> "OrganizationResponse":
        """Create OrganizationResponse from Organization model."""
        return cls(
            id=org.id,
            name=org.name,
            description=org.description,
            excerpt=org.excerpt,
            img_url=org.img_url,
            head_id=org.head_id,
            display_order=org.display_order,
            created_at=org.created_at,
            updated_at=org.updated_at,
            display_name=org.display_name,
            user_count=user_count,
            head_name=head_name
        )
    
    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseListResponse[OrganizationResponse]):
    """Standardized organization list response."""
    pass


class OrganizationSummary(BaseModel):
    """Schema for organization summary (lighter response)."""
    id: int
    name: str
    description: Optional[str] = None
    excerpt: Optional[str] = None
    img_url: Optional[str] = None
    display_order: int
    user_count: int = Field(default=0, description="Number of users")
    created_at: datetime
    
    @classmethod
    def from_organization_model(cls, org, user_count: int = 0) -> "OrganizationSummary":
        """Create OrganizationSummary from Organization model."""
        return cls(
            id=org.id,
            name=org.name,
            description=org.description,
            excerpt=org.excerpt,
            img_url=org.img_url,
            display_order=org.display_order,
            user_count=user_count,
            created_at=org.created_at
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
    sort_by: str = Field(default="display_order", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class DateRangeFilter(BaseModel):
    """Date range filter parameters."""
    
    start_date: Optional[date] = Field(default=None, description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date")


# ===== FILTER SCHEMAS =====

class OrganizationFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for organization listing."""
    
    # Organization-specific filters
    has_users: Optional[bool] = Field(None, description="Filter organizations with/without users")
    has_head: Optional[bool] = Field(None, description="Filter organizations with/without head")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in name or description")


# ===== HEAD ASSIGNMENT =====

class AssignHeadRequest(BaseModel):
    """Schema for assigning a head to an organization."""
    user_id: int = Field(..., description="ID of the user to assign as head")
    
    
class RemoveHeadRequest(BaseModel):
    """Schema for removing head from an organization."""
    confirm: bool = Field(..., description="Confirmation to remove head")