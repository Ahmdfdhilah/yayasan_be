"""Message schemas for request/response with input sanitization."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
from datetime import datetime
import re
import html

from src.schemas.shared import BaseListResponse
from src.models.message import MessageStatus


# ===== SANITIZATION UTILITIES =====

class SanitizationMixin:
    """Mixin for input sanitization methods."""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input to prevent XSS and clean up formatting."""
        if not text:
            return text
        
        # Strip whitespace
        text = text.strip()
        
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        
        # Remove any remaining HTML tags (in case they slipped through)
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
    @staticmethod
    def sanitize_multiline_text(text: str) -> str:
        """Sanitize multiline text (for message content)."""
        if not text:
            return text
        
        # Strip whitespace
        text = text.strip()
        
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        # Normalize line breaks but preserve structure
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove any HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        return text


# ===== BASE SCHEMAS =====

class MessageBase(BaseModel, SanitizationMixin):
    """Base message schema with sanitization."""
    email: EmailStr = Field(..., description="Sender email address")
    name: str = Field(..., min_length=1, max_length=255, description="Sender name")
    title: str = Field(..., min_length=1, max_length=500, description="Message title/subject")
    message: str = Field(..., min_length=1, max_length=5000, description="Message content")
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """Sanitize and validate name."""
        sanitized = cls.sanitize_text(name)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Name cannot be empty after sanitization")
        return sanitized
    
    @field_validator('title')
    @classmethod
    def sanitize_title(cls, title: str) -> str:
        """Sanitize and validate title."""
        sanitized = cls.sanitize_text(title)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Title cannot be empty after sanitization")
        return sanitized
    
    @field_validator('message')
    @classmethod
    def sanitize_message_content(cls, message: str) -> str:
        """Sanitize and validate message content."""
        sanitized = cls.sanitize_multiline_text(message)
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Message cannot be empty after sanitization")
        return sanitized


# ===== REQUEST SCHEMAS =====

class MessageCreate(MessageBase):
    """Schema for creating a message (public submission)."""
    pass


class MessageUpdate(BaseModel):
    """Schema for updating a message (admin only)."""
    status: Optional[MessageStatus] = None


class MessageStatusUpdate(BaseModel):
    """Schema for updating message status."""
    status: MessageStatus = Field(..., description="New message status")


# ===== RESPONSE SCHEMAS =====

class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    email: str
    name: str
    title: str
    message: str
    status: MessageStatus
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Computed fields
    is_unread: bool = Field(..., description="Whether message is unread")
    short_message: str = Field(..., description="Shortened message content")
    short_title: str = Field(..., description="Shortened title")
    
    @classmethod
    def from_message_model(cls, message) -> "MessageResponse":
        """Create MessageResponse from Message model."""
        return cls(
            id=message.id,
            email=message.email,
            name=message.name,
            title=message.title,
            message=message.message,
            status=message.status,
            ip_address=message.ip_address,
            user_agent=message.user_agent,
            read_at=message.read_at,
            created_at=message.created_at,
            updated_at=message.updated_at,
            created_by=message.created_by,
            updated_by=message.updated_by,
            is_unread=message.is_unread,
            short_message=message.short_message,
            short_title=message.short_title
        )
    
    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseListResponse[MessageResponse]):
    """Standardized message list response."""
    pass


class MessageSummary(BaseModel):
    """Schema for message summary (lighter response)."""
    id: int
    email: str
    name: str
    short_title: str
    status: MessageStatus
    is_unread: bool
    created_at: datetime
    
    @classmethod
    def from_message_model(cls, message) -> "MessageSummary":
        """Create MessageSummary from Message model."""
        return cls(
            id=message.id,
            email=message.email,
            name=message.name,
            short_title=message.short_title,
            status=message.status,
            is_unread=message.is_unread,
            created_at=message.created_at
        )
    
    model_config = ConfigDict(from_attributes=True)


class PublicMessageResponse(BaseModel):
    """Schema for public message submission response (limited info)."""
    id: int
    title: str
    status: str = "received"
    created_at: datetime
    message: str = "Thank you for your message. We will get back to you soon."
    
    @classmethod
    def from_message_model(cls, message) -> "PublicMessageResponse":
        """Create PublicMessageResponse from Message model."""
        return cls(
            id=message.id,
            title=message.title,
            created_at=message.created_at
        )


# ===== FILTER SCHEMAS =====

class MessageFilterParams(BaseModel):
    """Filter parameters for message listing."""
    
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    # Search and filtering
    search: Optional[str] = Field(default=None, description="Search in name, email, title, or message")
    status: Optional[MessageStatus] = Field(default=None, description="Filter by message status")
    unread_only: bool = Field(default=False, description="Show only unread messages")
    
    # Date filtering
    created_after: Optional[datetime] = Field(default=None, description="Filter messages created after this date")
    created_before: Optional[datetime] = Field(default=None, description="Filter messages created before this date")
    
    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


# ===== STATISTICS SCHEMAS =====

class MessageStatistics(BaseModel):
    """Message statistics schema."""
    total_messages: int
    unread_messages: int
    read_messages: int
    archived_messages: int
    messages_today: int
    messages_this_week: int
    messages_this_month: int