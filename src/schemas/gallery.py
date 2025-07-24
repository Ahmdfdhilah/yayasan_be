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
    is_active: bool = Field(default=True, description="Active status")
    display_order: int = Field(default=0, ge=0, description="Order for display")
    
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
    is_active: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)
    
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


class GalleryOrderUpdate(BaseModel):
    """Schema for updating gallery item order."""
    gallery_id: int = Field(..., description="Gallery item ID")
    new_order: int = Field(..., ge=0, description="New display order")


class GalleryBulkOrderUpdate(BaseModel):
    """Schema for bulk updating gallery order."""
    items: List[GalleryOrderUpdate] = Field(..., min_length=1, description="List of order updates")


# ===== RESPONSE SCHEMAS =====

class GalleryResponse(BaseModel):
    """Schema for gallery response."""
    id: int
    img_url: str
    title: str
    excerpt: Optional[str] = None
    is_active: bool
    display_order: int
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
            is_active=gallery.is_active,
            display_order=gallery.display_order,
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
    is_active: bool
    display_order: int
    
    @classmethod
    def from_gallery_model(cls, gallery) -> "GallerySummary":
        """Create GallerySummary from Gallery model."""
        return cls(
            id=gallery.id,
            img_url=gallery.img_url,
            title=gallery.title,
            is_active=gallery.is_active,
            display_order=gallery.display_order
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
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    
    # Sorting
    sort_by: str = Field(default="display_order", description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


# ===== ORDER RESPONSE SCHEMAS =====

class OrderUpdateResult(BaseModel):
    """Result of order update operation."""
    gallery_id: int
    old_order: int
    new_order: int
    success: bool
    message: Optional[str] = None


class BulkOrderUpdateResponse(BaseModel):
    """Response for bulk order update."""
    successful_updates: List[OrderUpdateResult]
    failed_updates: List[OrderUpdateResult]
    total_processed: int
    success_count: int
    failure_count: int