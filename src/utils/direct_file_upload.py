"""Direct file upload utilities without media_files table integration."""

from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, status, UploadFile, Form, File
import os
import uuid
from pathlib import Path
import mimetypes
import json

from src.core.config import settings


class DirectFileUploader:
    """Direct file upload handler that saves files and returns URLs without database storage."""
    
    def __init__(self, upload_base_path: str = "uploads"):
        """Initialize with base upload path."""
        self.upload_base_path = upload_base_path
    
    async def upload_file(
        self,
        file: UploadFile,
        subfolder: str = "images"
    ) -> str:
        """
        Upload file directly to filesystem and return URL.
        
        Args:
            file: UploadFile object
            subfolder: Subfolder within uploads directory
            
        Returns:
            URL path to the uploaded file
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Validate file
        await self._validate_file(file)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create upload directory path
        upload_dir = Path(settings.UPLOADS_PATH) / subfolder
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Full file path
        file_path = upload_dir / unique_filename
        
        try:
            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Return URL path (relative to static serving)
            return f"/static/uploads/{subfolder}/{unique_filename}"
            
        except Exception as e:
            # Clean up file if save fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file size (max 10MB for direct uploads)
        max_size = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum limit of 10MB"
            )
        
        # Check allowed file types
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )


def parse_json_form_data(data: str) -> Dict[str, Any]:
    """Parse JSON data from form field and handle datetime conversion."""
    from datetime import datetime
    
    try:
        parsed_data = json.loads(data)
        
        # Handle datetime fields that might have timezone info
        datetime_fields = ['published_at', 'created_at', 'updated_at']
        
        for field in datetime_fields:
            if field in parsed_data and parsed_data[field]:
                datetime_str = parsed_data[field]
                if isinstance(datetime_str, str):
                    try:
                        # Parse datetime and convert to naive datetime (remove timezone)
                        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        # Convert to naive datetime by removing timezone info
                        parsed_data[field] = dt.replace(tzinfo=None)
                    except ValueError:
                        # If parsing fails, keep original value
                        pass
        
        return parsed_data
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON data in form"
        )


# Dependency functions for each service
def get_board_member_multipart():
    """Dependency for board member multipart form data (image required)."""
    def _get_data(
        data: str = Form(..., description="JSON data for board member"),
        image: UploadFile = File(..., description="Profile image file (required)")
    ) -> Tuple[Dict[str, Any], UploadFile]:
        json_data = parse_json_form_data(data)
        return json_data, image
    return _get_data


def get_board_member_multipart_update():
    """Dependency for board member multipart form data (image optional for updates)."""
    def _get_data(
        data: str = Form(..., description="JSON data for board member"),
        image: Optional[UploadFile] = File(None, description="Profile image file (optional)")
    ) -> Tuple[Dict[str, Any], Optional[UploadFile]]:
        json_data = parse_json_form_data(data)
        return json_data, image
    return _get_data


def get_article_multipart():
    """Dependency for article multipart form data (image required)."""
    def _get_data(
        data: str = Form(..., description="JSON data for article"),
        image: UploadFile = File(..., description="Article image file (required)")
    ) -> Tuple[Dict[str, Any], UploadFile]:
        json_data = parse_json_form_data(data)
        return json_data, image
    return _get_data


def get_article_multipart_update():
    """Dependency for article multipart form data (image optional for updates)."""
    def _get_data(
        data: str = Form(..., description="JSON data for article"),
        image: Optional[UploadFile] = File(None, description="Article image file (optional)")
    ) -> Tuple[Dict[str, Any], Optional[UploadFile]]:
        json_data = parse_json_form_data(data)
        return json_data, image
    return _get_data


def get_gallery_multipart():
    """Dependency for gallery multipart form data."""
    def _get_data(
        data: str = Form(..., description="JSON data for gallery item"),
        image: UploadFile = File(..., description="Gallery image file")  # Required for gallery
    ) -> Tuple[Dict[str, Any], UploadFile]:
        json_data = parse_json_form_data(data)
        return json_data, image
    return _get_data


# Utility functions
async def process_image_upload(
    image: Optional[UploadFile],
    subfolder: str,
    uploader: DirectFileUploader
) -> Optional[str]:
    """Process image upload and return URL or None."""
    if not image:
        return None
    
    return await uploader.upload_file(image, subfolder)


def merge_data_with_image_url(json_data: Dict[str, Any], image_url: Optional[str]) -> Dict[str, Any]:
    """Merge JSON data with image URL."""
    if image_url:
        json_data["img_url"] = image_url
    return json_data