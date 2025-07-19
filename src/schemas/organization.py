"""Organization schemas for API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from src.models.enums import OrganizationType
from src.schemas.shared import BaseListResponse
from typing import Optional
from datetime import date
from pydantic import Field


# ===== BASE SCHEMAS =====

class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: Optional[str] = Field(None, max_length=255, description="URL-friendly slug")
    type: OrganizationType = Field(default=OrganizationType.SCHOOL, description="Organization type")
    description: Optional[str] = Field(None, description="Organization description")
    image_url: Optional[str] = Field(None, max_length=255, description="Organization image URL")
    website_url: Optional[str] = Field(None, max_length=255, description="Organization website URL")
    contact_info: Optional[Dict[str, Any]] = Field(None, description="Contact information as JSON")
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings as JSON")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate and normalize organization name."""
        return name.strip()
    
    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, url: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if url and not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url


# ===== REQUEST SCHEMAS =====

class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    type: Optional[OrganizationType] = None
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = Field(None, max_length=255)
    contact_info: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: Optional[str]) -> Optional[str]:
        """Validate and normalize organization name if provided."""
        return name.strip() if name else None
    
    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, url: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if url and not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url


# ===== RESPONSE SCHEMAS =====

class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    id: int
    name: str
    slug: Optional[str] = None
    type: OrganizationType
    description: Optional[str] = None
    image_url: Optional[str] = None
    website_url: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    display_name: str = Field(..., description="Display name for organization")
    user_count: int = Field(default=0, description="Number of users in organization")
    
    @classmethod
    def from_organization_model(cls, org, user_count: int = 0) -> "OrganizationResponse":
        """Create OrganizationResponse from Organization model."""
        return cls(
            id=org.id,
            name=org.name,
            slug=org.slug,
            type=org.type,
            description=org.description,
            image_url=org.image_url,
            website_url=org.website_url,
            contact_info=org.contact_info,
            settings=org.settings,
            created_at=org.created_at,
            updated_at=org.updated_at,
            display_name=org.display_name,
            user_count=user_count
        )
    
    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseListResponse[OrganizationResponse]):
    """Standardized organization list response."""
    pass


class OrganizationSummary(BaseModel):
    """Schema for organization summary (lighter response)."""
    id: int
    name: str
    type: OrganizationType
    description: Optional[str] = None
    user_count: int = Field(default=0, description="Number of users")
    created_at: datetime
    
    @classmethod
    def from_organization_model(cls, org, user_count: int = 0) -> "OrganizationSummary":
        """Create OrganizationSummary from Organization model."""
        return cls(
            id=org.id,
            name=org.name,
            type=org.type,
            description=org.description,
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
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class DateRangeFilter(BaseModel):
    """Date range filter parameters."""
    
    start_date: Optional[date] = Field(default=None, description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date")


# ===== FILTER SCHEMAS =====

class OrganizationFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for organization listing."""
    
    # Organization-specific filters
    type: Optional[OrganizationType] = Field(None, description="Filter by organization type")
    has_users: Optional[bool] = Field(None, description="Filter organizations with/without users")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in name, description, or contact info")


# ===== CONTACT INFO MANAGEMENT =====

class ContactInfoUpdate(BaseModel):
    """Schema for updating contact information."""
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)


class SettingsUpdate(BaseModel):
    """Schema for updating organization settings."""
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)
    academic_year_start: Optional[str] = Field(None, max_length=10, description="Format: MM-DD")
    evaluation_period_months: Optional[int] = Field(None, ge=1, le=12)
    auto_approve_rpps: Optional[bool] = Field(None)
    notification_emails: Optional[List[str]] = Field(None)