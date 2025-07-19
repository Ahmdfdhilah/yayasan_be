"""MediaFile schemas for API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from src.schemas.shared import BaseListResponse
from src.schemas.filters import PaginationParams, SearchParams, DateRangeFilter


# ===== BASE SCHEMAS =====

class MediaFileBase(BaseModel):
    """Base media file schema."""
    file_name: str = Field(..., min_length=1, max_length=255, description="Original file name")
    file_type: str = Field(..., min_length=1, max_length=50, description="File type/extension")
    mime_type: str = Field(..., max_length=100, description="MIME type")
    organization_id: Optional[int] = Field(None, description="Organization ID")
    file_metadata: Optional[Dict[str, Any]] = Field(None, description="File metadata as JSON")
    is_public: bool = Field(default=False, description="Whether file is publicly accessible")
    
    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, file_name: str) -> str:
        """Validate and normalize file name."""
        return file_name.strip()
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, file_type: str) -> str:
        """Validate and normalize file type."""
        return file_type.lower().strip()


# ===== REQUEST SCHEMAS =====

class MediaFileCreate(MediaFileBase):
    """Schema for creating a media file record."""
    file_path: str = Field(..., min_length=1, max_length=255, description="File storage path")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    uploader_id: Optional[int] = Field(None, description="Uploader user ID")


class MediaFileUpdate(BaseModel):
    """Schema for updating a media file."""
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    file_metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    organization_id: Optional[int] = None
    
    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, file_name: Optional[str]) -> Optional[str]:
        """Validate and normalize file name if provided."""
        return file_name.strip() if file_name else None


class MediaFileUpload(BaseModel):
    """Schema for file upload request."""
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., ge=0, le=100*1024*1024, description="File size in bytes (max 100MB)")
    mime_type: str = Field(..., description="MIME type")
    organization_id: Optional[int] = None
    is_public: bool = Field(default=False)
    metadata: Optional[Dict[str, Any]] = None


# ===== RESPONSE SCHEMAS =====

class MediaFileResponse(BaseModel):
    """Schema for media file response."""
    id: int
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    mime_type: str
    uploader_id: Optional[int] = None
    organization_id: Optional[int] = None
    file_metadata: Optional[Dict[str, Any]] = None
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    display_name: str = Field(..., description="Display name for file")
    extension: str = Field(..., description="File extension")
    file_size_formatted: str = Field(..., description="Human-readable file size")
    file_category: str = Field(..., description="File category")
    can_preview: bool = Field(..., description="Whether file can be previewed")
    
    # Related data
    uploader_name: Optional[str] = Field(None, description="Uploader name")
    organization_name: Optional[str] = Field(None, description="Organization name")
    
    @classmethod
    def from_media_file_model(cls, media_file, include_relations: bool = False) -> "MediaFileResponse":
        """Create MediaFileResponse from MediaFile model."""
        data = {
            "id": media_file.id,
            "file_path": media_file.file_path,
            "file_name": media_file.file_name,
            "file_type": media_file.file_type,
            "file_size": media_file.file_size,
            "mime_type": media_file.mime_type,
            "uploader_id": media_file.uploader_id,
            "organization_id": media_file.organization_id,
            "file_metadata": media_file.file_metadata,
            "is_public": media_file.is_public,
            "created_at": media_file.created_at,
            "updated_at": media_file.updated_at,
            "display_name": media_file.display_name,
            "extension": media_file.extension,
            "file_size_formatted": media_file.get_formatted_size(),
            "file_category": media_file.get_file_category(),
            "can_preview": media_file.can_be_viewed_inline()
        }
        
        if include_relations:
            data.update({
                "uploader_name": media_file.uploader.display_name if hasattr(media_file, 'uploader') and media_file.uploader else None,
                "organization_name": media_file.organization.name if hasattr(media_file, 'organization') and media_file.organization else None
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class MediaFileUploadResponse(BaseModel):
    """Schema for media file upload response."""
    id: int
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: str
    is_public: bool
    upload_url: str
    message: str


class MediaFileListResponse(BaseListResponse[MediaFileResponse]):
    """Standardized media file list response."""
    pass


class MediaFileSummary(BaseModel):
    """Schema for media file summary (lighter response)."""
    id: int
    file_name: str
    file_type: str
    file_size: int
    is_public: bool
    created_at: datetime
    
    # Computed fields
    file_size_formatted: str
    file_category: str
    
    @classmethod
    def from_media_file_model(cls, media_file) -> "MediaFileSummary":
        """Create MediaFileSummary from MediaFile model."""
        return cls(
            id=media_file.id,
            file_name=media_file.file_name,
            file_type=media_file.file_type,
            file_size=media_file.file_size,
            is_public=media_file.is_public,
            created_at=media_file.created_at,
            file_size_formatted=media_file.get_formatted_size(),
            file_category=media_file.get_file_category()
        )
    
    model_config = {"from_attributes": True}


# ===== FILTER SCHEMAS =====

class MediaFileFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for media file listing."""
    
    # File-specific filters
    file_type: Optional[str] = Field(None, description="Filter by file type/extension")
    file_category: Optional[str] = Field(None, description="Filter by file category (image, document, etc.)")
    uploader_id: Optional[int] = Field(None, description="Filter by uploader user ID")
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    is_public: Optional[bool] = Field(None, description="Filter by public/private status")
    min_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in file name or metadata")
    
    # Override default sort
    sort_by: str = Field(default="created_at", description="Sort field")


# ===== FILE MANAGEMENT SCHEMAS =====

class FileUrlResponse(BaseModel):
    """Schema for file URL response."""
    file_id: int
    file_name: str
    file_url: str
    thumbnail_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class FileBulkDelete(BaseModel):
    """Schema for bulk file deletion."""
    file_ids: List[int] = Field(..., min_items=1, description="List of file IDs to delete")
    force_delete: bool = Field(default=False, description="Force delete even if file has dependencies")


class FileBulkUpdate(BaseModel):
    """Schema for bulk file updates."""
    file_ids: List[int] = Field(..., min_items=1, description="List of file IDs to update")
    is_public: Optional[bool] = None
    organization_id: Optional[int] = None


class FileMetadataUpdate(BaseModel):
    """Schema for updating file metadata."""
    metadata: Dict[str, Any] = Field(..., description="Metadata key-value pairs")


# ===== ANALYTICS SCHEMAS =====

class FileStorageAnalytics(BaseModel):
    """Schema for file storage analytics."""
    total_files: int
    total_size_bytes: int
    total_size_formatted: str
    by_type: Dict[str, Dict[str, Any]] = Field(description="Statistics by file type")
    by_category: Dict[str, Dict[str, Any]] = Field(description="Statistics by file category")
    by_organization: Dict[str, Dict[str, Any]] = Field(description="Statistics by organization")
    public_files: int
    private_files: int
    recent_uploads: int = Field(description="Uploads in last 7 days")


class FileUploadStats(BaseModel):
    """Schema for file upload statistics."""
    uploads_today: int
    uploads_this_week: int
    uploads_this_month: int
    uploads_by_day: Dict[str, int] = Field(description="Uploads per day (last 30 days)")
    top_uploaders: List[Dict[str, Any]] = Field(description="Top file uploaders")
    popular_file_types: List[Dict[str, Any]] = Field(description="Most common file types")