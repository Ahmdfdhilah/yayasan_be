"""Media file API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from src.core.database import get_db
from src.auth.permissions import get_current_active_user
from src.services.media_file import MediaFileService
from src.repositories.media_file import MediaFileRepository
from src.schemas.media_file import (
    MediaFileResponse, MediaFileListResponse, MediaFileUpdate,
    MediaFileUploadResponse, MediaFileViewResponse
)
from src.schemas.shared import MessageResponse
from src.schemas.media_file import MediaFileFilterParams
from src.utils.messages import get_message

router = APIRouter(prefix="/media-files", tags=["Media Files"])


def get_media_file_service(db: AsyncSession = Depends(get_db)) -> MediaFileService:
    """Get media file service dependency."""
    media_file_repo = MediaFileRepository(db)
    return MediaFileService(media_file_repo)


@router.post("/upload", response_model=MediaFileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    is_public: bool = False,
    current_user: dict = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Upload a new media file.
    
    **Required permissions:** authenticated user
    
    **Body:**
    - file: File to upload (multipart/form-data)
    - is_public: Whether file should be publicly accessible (optional, default: false)
    
    **Returns:** Media file upload response with download URL
    """
    return await service.upload_file(
        file=file,
        uploader_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        is_public=is_public
    )


@router.get("", response_model=MediaFileListResponse)
async def list_media_files(
    filters: MediaFileFilterParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    List media files with pagination and filtering.
    
    **Required permissions:** authenticated user
    
    **Query Parameters:**
    - page: Page number (default: 1)
    - size: Items per page (default: 10, max: 100)
    - q: Search in file names
    - file_type: Filter by file type/extension
    - file_category: Filter by file category
    - uploader_id: Filter by uploader user ID
    - organization_id: Filter by organization ID  
    - is_public: Filter by public/private status
    - min_size: Minimum file size in bytes
    - max_size: Maximum file size in bytes
    - start_date: Filter files created after this date
    - end_date: Filter files created before this date
    - sort_by: Sort field (default: created_at)
    - sort_order: Sort order - asc/desc (default: desc)
    
    **Returns:** Paginated list of media files
    """
    # Regular users can only see their own files and public files
    user_roles = current_user.get("roles", [])
    is_admin = any(role in ["admin"] for role in user_roles)
    
    if not is_admin:
        # Regular users: filter to own files or public files
        if not filters.uploader_id and not filters.is_public:
            filters.uploader_id = current_user["id"]
    
    return await service.list_files(
        filters=filters,
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id")
    )


# Specific routes first to avoid conflicts with parameterized routes

@router.get("/uploader/{uploader_id}", response_model=MediaFileListResponse)
async def get_files_by_uploader(
    uploader_id: int,
    filters: MediaFileFilterParams = Depends(),
    current_user: dict = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Get files uploaded by specific user.
    
    **Required permissions:** admin, content manager, or the uploader themselves
    
    **Path Parameters:**
    - uploader_id: User ID of the uploader
    
    **Query Parameters:** Same as list_media_files
    
    **Returns:** Paginated list of media files uploaded by the specified user
    """
    # Check permissions: admin/content manager or the uploader themselves
    user_roles = current_user.get("roles", [])
    is_admin = any(role in ["admin"] for role in user_roles)
    
    if not is_admin and current_user["id"] != uploader_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("access", "not_authorized_view_files")
        )
    
    return await service.get_files_by_uploader(
        uploader_id=uploader_id,
        filters=filters
    )


@router.get("/public/list", response_model=MediaFileListResponse)
async def list_public_files(
    filters: MediaFileFilterParams = Depends(),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    List public media files (no authentication required).
    
    **Required permissions:** none (public endpoint)
    
    **Query Parameters:** Same as list_media_files
    
    **Returns:** Paginated list of public media files
    """
    return await service.get_public_files(filters=filters)


# Parameterized routes come last to avoid conflicts

@router.get("/{file_id}", response_model=MediaFileResponse)
async def get_media_file(
    file_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Get media file details by ID.
    
    **Required permissions:** authenticated user (with access to the file)
    
    **Path Parameters:**
    - file_id: Media file ID
    
    **Returns:** Media file details
    """
    return await service.get_file(file_id=file_id, user_id=current_user["id"])


@router.get("/{file_id}/view", response_model=MediaFileViewResponse)
async def get_file_view_info(
    file_id: int,
    current_user: Optional[dict] = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Get file view information with static URL path.
    
    **Required permissions:** authenticated user (for private files) or public access (for public files)
    
    **Path Parameters:**
    - file_id: Media file ID
    
    **Returns:** File view information with static URL for direct access
    """
    user_id = current_user["id"] if current_user else None
    return await service.get_file_view_info(file_id=file_id, user_id=user_id)


@router.get("/{file_id}/download")
async def download_media_file(
    file_id: int,
    current_user: Optional[dict] = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Download media file content.
    
    **Required permissions:** authenticated user (for private files) or public access (for public files)
    
    **Path Parameters:**
    - file_id: Media file ID
    
    **Returns:** File content with appropriate headers for download
    """
    user_id = current_user["id"] if current_user else None
    content, filename, mime_type = await service.get_file_content(
        file_id=file_id, 
        user_id=user_id
    )
    
    # Create streaming response
    return StreamingResponse(
        io.BytesIO(content),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Length": str(len(content))
        }
    )


@router.put("/{file_id}", response_model=MediaFileResponse)
async def update_media_file(
    file_id: int,
    file_data: MediaFileUpdate,
    current_user: dict = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Update media file metadata.
    
    **Required permissions:** file owner, admin, or content manager
    
    **Path Parameters:**
    - file_id: Media file ID
    
    **Body:** Media file update data
    - file_metadata: Updated file metadata (optional)
    - is_public: Updated public status (optional)
    
    **Returns:** Updated media file details
    """
    return await service.update_file(
        file_id=file_id,
        file_data=file_data,
        user_id=current_user["id"]
    )


@router.delete("/{file_id}", response_model=MessageResponse)
async def delete_media_file(
    file_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: MediaFileService = Depends(get_media_file_service)
):
    """
    Delete media file and remove from filesystem.
    
    **Required permissions:** file owner, admin, or content manager
    
    **Path Parameters:**
    - file_id: Media file ID
    
    **Returns:** Success message
    """
    return await service.delete_file(file_id=file_id, user_id=current_user["id"])


# Duplicate routes removed - moved to above to fix routing conflicts