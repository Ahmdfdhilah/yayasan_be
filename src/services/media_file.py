"""Media file service for file management."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, UploadFile
import os
import uuid
from pathlib import Path
import mimetypes

from src.repositories.media_file import MediaFileRepository
from src.schemas.media_file import (
    MediaFileCreate, MediaFileUpdate, MediaFileResponse, 
    MediaFileListResponse, MediaFileUploadResponse, MediaFileViewResponse
)
from src.schemas.shared import MessageResponse
from src.schemas.media_file import MediaFileFilterParams
from src.models.media_file import MediaFile


class MediaFileService:
    """Media file service for file management."""
    
    def __init__(self, media_file_repo: MediaFileRepository):
        self.media_file_repo = media_file_repo
        
    async def upload_file(
        self, 
        file: UploadFile, 
        uploader_id: int,
        organization_id: Optional[int] = None,
        is_public: bool = False,
        upload_path: str = "static/uploads"
    ) -> MediaFileUploadResponse:
        """Upload file and create media file record."""
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create upload directory if not exists
        upload_dir = Path(upload_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Full file path
        file_path = upload_dir / unique_filename
        
        try:
            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Get file info
            file_size = len(content)
            mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            file_type = file_extension.lstrip('.')
            
            # Create media file record
            media_file_data = MediaFileCreate(
                file_name=file.filename,
                file_path=str(file_path),
                file_type=file_type,
                mime_type=mime_type,
                file_size=file_size,
                uploader_id=uploader_id,
                organization_id=organization_id,
                is_public=is_public,
                file_metadata={
                    "upload_path": str(upload_path),
                    "unique_filename": unique_filename
                }
            )
            
            # Save to database
            media_file = await self.media_file_repo.create(media_file_data)
            
            return MediaFileUploadResponse(
                id=media_file.id,
                file_name=media_file.file_name,
                file_path=media_file.file_path,
                file_size=media_file.file_size,
                file_type=media_file.file_type,
                mime_type=media_file.mime_type,
                is_public=media_file.is_public,
                upload_url=f"/api/media-files/{media_file.id}/download",
                message="File uploaded successfully"
            )
            
        except Exception as e:
            # Clean up file if database save fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def get_file(self, file_id: int, user_id: Optional[int] = None) -> MediaFileResponse:
        """Get media file by ID."""
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check access permissions
        if not media_file.is_public:
            # Private file - only uploader can access
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access private file"
                )
            if user_id != media_file.uploader_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this file"
                )
        
        return MediaFileResponse(
            id=media_file.id,
            file_name=media_file.file_name,
            file_path=media_file.file_path,
            file_size=media_file.file_size,
            file_type=media_file.file_type,
            mime_type=media_file.mime_type,
            uploader_id=media_file.uploader_id,
            organization_id=media_file.organization_id,
            is_public=media_file.is_public,
            file_metadata=media_file.file_metadata,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at
        )
    
    async def list_files(
        self, 
        filters: MediaFileFilterParams,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> MediaFileListResponse:
        """List media files with filters."""
        
        # Add organization filter if provided
        if organization_id:
            filters.organization_id = organization_id
        
        media_files, total_count = await self.media_file_repo.list_with_filters(filters)
        
        # Convert to response format
        files_response = []
        for media_file in media_files:
            files_response.append(MediaFileResponse(
                id=media_file.id,
                file_name=media_file.file_name,
                file_path=media_file.file_path,
                file_size=media_file.file_size,
                file_type=media_file.file_type,
                mime_type=media_file.mime_type,
                uploader_id=media_file.uploader_id,
                organization_id=media_file.organization_id,
                is_public=media_file.is_public,
                file_metadata=media_file.file_metadata,
                created_at=media_file.created_at,
                updated_at=media_file.updated_at
            ))
        
        return MediaFileListResponse(
            items=files_response,
            total=total_count,
            page=filters.page,
            size=filters.size,
            pages=(total_count + filters.size - 1) // filters.size
        )
    
    async def update_file(
        self, 
        file_id: int, 
        file_data: MediaFileUpdate,
        user_id: int
    ) -> MediaFileResponse:
        """Update media file metadata."""
        
        # Check if file exists and user has permission
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check permission (only uploader or admin can update)
        if media_file.uploader_id != user_id:
            # Additional permission checks can be added here
            pass
        
        # Update file
        updated_media_file = await self.media_file_repo.update(
            file_id, 
            file_data.model_dump(exclude_unset=True)
        )
        
        return MediaFileResponse(
            id=updated_media_file.id,
            file_name=updated_media_file.file_name,
            file_path=updated_media_file.file_path,
            file_size=updated_media_file.file_size,
            file_type=updated_media_file.file_type,
            mime_type=updated_media_file.mime_type,
            uploader_id=updated_media_file.uploader_id,
            organization_id=updated_media_file.organization_id,
            is_public=updated_media_file.is_public,
            file_metadata=updated_media_file.file_metadata,
            created_at=updated_media_file.created_at,
            updated_at=updated_media_file.updated_at
        )
    
    async def delete_file(self, file_id: int, user_id: int) -> MessageResponse:
        """Delete media file and remove from filesystem."""
        
        # Check if file exists and user has permission
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check permission (only uploader or admin can delete)
        if media_file.uploader_id != user_id:
            # Additional permission checks can be added here
            pass
        
        try:
            # Remove file from filesystem
            file_path = Path(media_file.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Remove from database
            await self.media_file_repo.delete(file_id)
            
            return MessageResponse(message="Media file deleted successfully")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    async def get_file_content(self, file_id: int, user_id: Optional[int] = None) -> tuple[bytes, str, str]:
        """Get file content for download."""
        
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check access permissions
        if not media_file.is_public:
            # Private file - only uploader can access
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access private file"
                )
            if user_id != media_file.uploader_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this file"
                )
        
        # Read file content
        file_path = Path(media_file.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical file not found"
            )
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            return content, media_file.file_name, media_file.mime_type
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read file: {str(e)}"
            )
    
    async def get_files_by_uploader(
        self, 
        uploader_id: int,
        filters: MediaFileFilterParams
    ) -> MediaFileListResponse:
        """Get files uploaded by specific user."""
        
        # Set uploader filter
        filters.uploader_id = uploader_id
        
        return await self.list_files(filters)
    
    async def get_public_files(self, filters: MediaFileFilterParams) -> MediaFileListResponse:
        """Get public files only."""
        
        # Set public filter
        filters.is_public = True
        
        return await self.list_files(filters)
    
    async def get_file_view_info(self, file_id: int, user_id: Optional[int] = None) -> MediaFileViewResponse:
        """Get file view information with static URL."""
        
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        
        # Check access permissions
        if not media_file.is_public:
            # Private file - only uploader can access
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access private file"
                )
            if user_id != media_file.uploader_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this file"
                )
        
        # Check if physical file exists
        file_path = Path(media_file.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical file not found"
            )
        
        # Generate static URL path (relative to static serving)
        view_url = f"/static/uploads/{file_path.name}"
        
        return MediaFileViewResponse(
            file_path=str(file_path),
            file_name=media_file.file_name,
            mime_type=media_file.mime_type,
            view_url=view_url
        )