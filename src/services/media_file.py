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
from src.utils.messages import get_message


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
        upload_path: str = None
    ) -> MediaFileUploadResponse:
        """Upload file and create media file record."""
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_message("file", "upload_failed")
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Use consistent upload path from settings
        if upload_path is None:
            from src.core.config import settings
            upload_path = settings.UPLOADS_PATH
        
        # Create upload directory if not exists
        upload_dir = Path(upload_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Full file path for storage
        file_path = upload_dir / unique_filename
        
        # Web-compatible path for database (always forward slashes)
        web_path = f"{upload_path}/{unique_filename}".replace("\\", "/")
        
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
                file_path=web_path,
                file_type=file_type,
                mime_type=mime_type,
                file_size=file_size,
                uploader_id=uploader_id,
                organization_id=organization_id,
                is_public=is_public,
                file_metadata={
                    "upload_path": upload_path.replace("\\", "/"),
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
                message="File berhasil diunggah"
            )
            
        except Exception as e:
            # Clean up file if database save fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=get_message("file", "upload_failed")
            )
    
    async def get_file(
        self, 
        file_id: int, 
        user_id: Optional[int] = None,
        user_role: str = None,
        user_organization_id: Optional[int] = None
    ) -> MediaFileResponse:
        """Get media file by ID."""
        media_file = await self.media_file_repo.get_by_id(file_id)
       
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("file", "file_not_found")
            )
        
        # Check access permissions
        if not media_file.is_public:
            # Private file - check based on role
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autentikasi diperlukan untuk mengakses file pribadi"
                )
            
            has_access = False
            user_role = user_role or "guru"
            
            # Admin has full access
            if user_role in ["admin", "ADMIN", "SUPER_ADMIN"]:
                has_access = True
            # Kepala sekolah can access files from same organization
            elif user_role in ["kepala_sekolah", "KEPALA_SEKOLAH"]:
                if user_organization_id and media_file.organization_id == user_organization_id:
                    has_access = True
            # Guru can only access their own files
            elif user_role in ["guru", "GURU"]:
                if media_file.uploader_id == user_id:
                    has_access = True
            # File uploader can always access their own file
            elif media_file.uploader_id == user_id:
                has_access = True
                
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tidak memiliki otorisasi untuk mengakses file ini"
                )
        
        return MediaFileResponse.from_media_file_model(media_file, include_relations=True)
    
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
        
        media_files, total_count = await self.media_file_repo.get_all_files_filtered(filters)
        
        # Convert to response format
        files_response = []
        for media_file in media_files:
            files_response.append(MediaFileResponse.from_media_file_model(media_file, include_relations=True))
        
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
        user_id: int,
        user_role: str = None,
        user_organization_id: Optional[int] = None
    ) -> MediaFileResponse:
        """Update media file metadata."""
        
        # Check if file exists and user has permission
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("file", "file_not_found")
            )
        
        # Check access permissions
        has_access = False
        user_role = user_role or "guru"
        
        # Admin has full access
        if user_role in ["admin", "ADMIN", "SUPER_ADMIN"]:
            has_access = True
        # Kepala sekolah can update files from same organization
        elif user_role in ["kepala_sekolah", "KEPALA_SEKOLAH"]:
            if user_organization_id and media_file.organization_id == user_organization_id:
                has_access = True
        # Guru can only update their own files
        elif user_role in ["guru", "GURU"]:
            if media_file.uploader_id == user_id:
                has_access = True
        # File uploader can always update their own file
        elif media_file.uploader_id == user_id:
            has_access = True
            
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki otorisasi untuk mengupdate file ini"
            )
        
        # Update file
        updated_media_file = await self.media_file_repo.update(
            file_id, 
            file_data.model_dump(exclude_unset=True)
        )
        
        return MediaFileResponse.from_media_file_model(updated_media_file, include_relations=True)
    
    async def delete_file(
        self, 
        file_id: int, 
        user_id: int,
        user_role: str = None,
        user_organization_id: Optional[int] = None
    ) -> MessageResponse:
        """Delete media file and remove from filesystem."""
        
        # Check if file exists and user has permission
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("file", "file_not_found")
            )
        
        # Check access permissions
        has_access = False
        user_role = user_role or "guru"
        
        # Admin has full access
        if user_role in ["admin", "ADMIN", "SUPER_ADMIN"]:
            has_access = True
        # Kepala sekolah can delete files from same organization
        elif user_role in ["kepala_sekolah", "KEPALA_SEKOLAH"]:
            if user_organization_id and media_file.organization_id == user_organization_id:
                has_access = True
        # Guru can only delete their own files
        elif user_role in ["guru", "GURU"]:
            if media_file.uploader_id == user_id:
                has_access = True
        # File uploader can always delete their own file
        elif media_file.uploader_id == user_id:
            has_access = True
            
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki otorisasi untuk menghapus file ini"
            )
        
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
    
    async def get_file_content(
        self, 
        file_id: int, 
        user_id: Optional[int] = None,
        user_role: str = None,
        user_organization_id: Optional[int] = None
    ) -> tuple[bytes, str, str]:
        """Get file content for download."""
        
        media_file = await self.media_file_repo.get_by_id(file_id)
     
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("file", "file_not_found")
            )
        
        # Check access permissions
        if not media_file.is_public:
            # Private file - check based on role
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autentikasi diperlukan untuk mengakses file pribadi"
                )
            
            has_access = False
            user_role = user_role or "guru"
            
            # Admin has full access
            if user_role in ["admin", "ADMIN", "SUPER_ADMIN"]:
                has_access = True
            # Kepala sekolah can access files from same organization
            elif user_role in ["kepala_sekolah", "KEPALA_SEKOLAH"]:
                if user_organization_id and media_file.organization_id == user_organization_id:
                    has_access = True
            # Guru can only access their own files
            elif user_role in ["guru", "GURU"]:
                if media_file.uploader_id == user_id:
                    has_access = True
            # File uploader can always access their own file
            elif media_file.uploader_id == user_id:
                has_access = True
                
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tidak memiliki otorisasi untuk mengakses file ini"
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
    
    async def get_file_view_info(
        self, 
        file_id: int, 
        user_id: Optional[int] = None,
        user_role: str = None,
        user_organization_id: Optional[int] = None
    ) -> MediaFileViewResponse:
        """Get file view information with static URL."""
        
        media_file = await self.media_file_repo.get_by_id(file_id)
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("file", "file_not_found")
            )
        
        # Check access permissions
        if not media_file.is_public:
            # Private file - check based on role
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autentikasi diperlukan untuk mengakses file pribadi"
                )
            
            has_access = False
            user_role = user_role or "guru"
            
            # Admin has full access
            if user_role in ["admin", "ADMIN", "SUPER_ADMIN"]:
                has_access = True
            # Kepala sekolah can access files from same organization
            elif user_role in ["kepala_sekolah", "KEPALA_SEKOLAH"]:
                if user_organization_id and media_file.organization_id == user_organization_id:
                    has_access = True
            # Guru can only access their own files
            elif user_role in ["guru", "GURU"]:
                if media_file.uploader_id == user_id:
                    has_access = True
            # File uploader can always access their own file
            elif media_file.uploader_id == user_id:
                has_access = True
                
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tidak memiliki otorisasi untuk mengakses file ini"
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