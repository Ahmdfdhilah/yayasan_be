"""Gallery schemas for request/response."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.schemas.shared import BaseListResponse


# ===== BASE SCHEMAS =====

class GalleryBase(BaseModel):
    """Base gallery schema."""
    img_url: str = Field(..., min_length=1, max_length=500, description="Image URL")
    title: str = Field(..., min_length=1, max_length=255, description="Image title")
    excerpt: Optional[str] = Field(None, max_length=500, description="Short description")
    is_highlight: bool = Field(default=False, description="Whether this gallery item is highlighted")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate and clean title."""
        return title.strip()
    
    @field_validator('img_url')
    @classmethod
    def validate_img_url(cls, img_url: str) -> str:
        """Validate and clean image URL."""
        return img_url.strip()


# ===== REQUEST SCHEMAS =====

class GalleryCreate(GalleryBase):
    """Schema for creating a gallery item."""
    pass


class GalleryUpdate(BaseModel):
    """Schema for updating a gallery item."""
    img_url: Optional[str] = Field(None, min_length=1, max_length=500)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    is_highlight: Optional[bool] = Field(None, description="Whether this gallery item is highlighted")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, title: Optional[str]) -> Optional[str]:
        """Validate and clean title if provided."""
        return title.strip() if title else None
    
    @field_validator('img_url')
    @classmethod
    def validate_img_url(cls, img_url: Optional[str]) -> Optional[str]:
        """Validate and clean image URL if provided."""
        return img_url.strip() if img_url else None




# ===== RESPONSE SCHEMAS =====

class GalleryResponse(BaseModel):
    """Schema for gallery response."""
    id: int
    img_url: str
    title: str
    excerpt: Optional[str] = None
    is_highlight: bool
    created_at: str
    updated_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Computed fields
    short_excerpt: str = Field(..., description="Shortened excerpt")
    
    @classmethod
    def from_gallery_model(cls, gallery) -> "GalleryResponse":
        """Create GalleryResponse from Gallery model."""
        return cls(
            id=gallery.id,
            img_url=gallery.img_url,
            title=gallery.title,
            excerpt=gallery.excerpt,
            is_highlight=gallery.is_highlight,
            created_at=gallery.created_at.isoformat() if gallery.created_at else "",
            updated_at=gallery.updated_at.isoformat() if gallery.updated_at else None,
            created_by=gallery.created_by,
            updated_by=gallery.updated_by,
            short_excerpt=gallery.short_excerpt
        )
    
    model_config = ConfigDict(from_attributes=True)


class GalleryListResponse(BaseListResponse[GalleryResponse]):
    """Standardized gallery list response."""
    pass


class GallerySummary(BaseModel):
    """Schema for gallery summary (lighter response)."""
    id: int
    img_url: str
    title: str
    is_highlight: bool
    
    @classmethod
    def from_gallery_model(cls, gallery) -> "GallerySummary":
        """Create GallerySummary from Gallery model."""
        return cls(
            id=gallery.id,
            img_url=gallery.img_url,
            title=gallery.title,
            is_highlight=gallery.is_highlight
        )
    
    model_config = ConfigDict(from_attributes=True)


# ===== FILTER SCHEMAS =====

class GalleryFilterParams(BaseModel):
    """Filter parameters for gallery listing."""
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Search and filtering
    search: Optional[str] = Field(default=None, description="Search in title")
    is_highlighted: Optional[bool] = Field(default=None, description="Filter by highlight status")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


