"""MediaFile model for unified file management."""

from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, JSON, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization
    from .rpp_submission import RPPSubmission
    from .rpp_submission_item import RPPSubmissionItem


class MediaFile(BaseModel, SQLModel, table=True):
    """Media file model for unified file management."""
    
    __tablename__ = "media_files"
    
    id: int = Field(primary_key=True)
    file_path: str = Field(max_length=255, nullable=False, index=True)
    file_name: str = Field(max_length=255, nullable=False)
    file_type: str = Field(max_length=50, nullable=False, index=True)
    file_size: int = Field(nullable=False, description="File size in bytes")
    mime_type: str = Field(max_length=100, nullable=False)
    
    # File ownership and organization
    uploader_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True
    )
    organization_id: Optional[int] = Field(
        default=None,
        foreign_key="organizations.id",
        index=True
    )
    
    # File metadata and visibility
    file_metadata: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, comment="File metadata: width, height, duration, etc")
    )
    is_public: bool = Field(default=False, index=True)
    
    # Relationships
    uploader: Optional["User"] = Relationship(back_populates="uploaded_files")
    organization: Optional["Organization"] = Relationship(back_populates="media_files")
    rpp_submissions: List["RPPSubmission"] = Relationship(back_populates="file")
    rpp_submission_items: List["RPPSubmissionItem"] = Relationship(back_populates="file")
    
    def __repr__(self) -> str:
        return f"<MediaFile(id={self.id}, file_name={self.file_name}, type={self.file_type})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the file."""
        return self.file_name
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''
    
    @property
    def file_size_kb(self) -> float:
        """Get file size in KB."""
        return self.file_size / 1024
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)
    
    def is_image(self) -> bool:
        """Check if file is an image."""
        image_types = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
        return self.extension in image_types
    
    def is_document(self) -> bool:
        """Check if file is a document."""
        document_types = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
        return self.extension in document_types
    
    def is_video(self) -> bool:
        """Check if file is a video."""
        video_types = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
        return self.extension in video_types
    
    def is_audio(self) -> bool:
        """Check if file is audio."""
        audio_types = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma']
        return self.extension in audio_types
    
    def get_metadata_field(self, key: str) -> Optional[str]:
        """Get specific metadata field."""
        if self.file_metadata and isinstance(self.file_metadata, dict):
            return self.file_metadata.get(key)
        return None
    
    def update_metadata_field(self, key: str, value: str) -> None:
        """Update specific metadata field."""
        if self.file_metadata is None:
            self.file_metadata = {}
        self.file_metadata[key] = value
    
    def get_url(self, base_url: str = "") -> str:
        """Get file URL."""
        return f"{base_url.rstrip('/')}/{self.file_path}"
    
    def get_thumbnail_url(self, base_url: str = "") -> Optional[str]:
        """Get thumbnail URL if available."""
        if self.is_image():
            # Assuming thumbnails are stored with _thumb suffix
            path_parts = self.file_path.rsplit('.', 1)
            if len(path_parts) == 2:
                thumb_path = f"{path_parts[0]}_thumb.{path_parts[1]}"
                return f"{base_url.rstrip('/')}/{thumb_path}"
        return None
    
    def get_formatted_size(self) -> str:
        """Get formatted file size string."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size_kb:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size_mb:.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    def can_be_viewed_inline(self) -> bool:
        """Check if file can be viewed inline in browser."""
        inline_types = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt', 'svg']
        return self.extension in inline_types
    
    def get_file_category(self) -> str:
        """Get file category based on type."""
        if self.is_image():
            return "image"
        elif self.is_document():
            return "document"
        elif self.is_video():
            return "video"
        elif self.is_audio():
            return "audio"
        else:
            return "other"