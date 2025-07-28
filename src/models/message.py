"""Message model for public contact submissions."""

from typing import Optional
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Enum as SQLEnum, Column

from .base import BaseModel
from .enums import MessagePriority


class MessageStatus(str, Enum):
    """Message status enumeration."""
    UNREAD = "UNREAD"
    READ = "READ"
    ARCHIVED = "ARCHIEVED"


class Message(BaseModel, SQLModel, table=True):
    """Message model for public contact submissions."""
    
    __tablename__ = "messages"
    
    id: int = Field(primary_key=True)
    email: str = Field(max_length=255, nullable=False, index=True, description="Sender email")
    name: str = Field(max_length=255, nullable=False, index=True, description="Sender name")
    title: str = Field(max_length=500, nullable=False, index=True, description="Message title/subject")
    message: str = Field(nullable=False, description="Message content")
    
    # Message metadata
    status: MessageStatus = Field(
        sa_column=Column(SQLEnum(MessageStatus), nullable=False, default=MessageStatus.UNREAD),
        description="Message status"
    )
    
    # Tracking fields
    ip_address: Optional[str] = Field(max_length=45, default=None, description="Sender IP address")
    user_agent: Optional[str] = Field(max_length=500, default=None, description="Sender user agent")
    read_at: Optional[datetime] = Field(default=None, description="When message was first read")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, email={self.email}, title={self.title[:50]}, status={self.status.value})>"
    
    @property
    def is_unread(self) -> bool:
        """Check if message is unread."""
        return self.status == MessageStatus.UNREAD
    
    @property
    def short_message(self) -> str:
        """Get shortened message content."""
        if not self.message:
            return ""
        return (self.message[:100] + "...") if len(self.message) > 100 else self.message
    
    @property
    def short_title(self) -> str:
        """Get shortened title."""
        if not self.title:
            return ""
        return (self.title[:50] + "...") if len(self.title) > 50 else self.title
    
    def mark_as_read(self, read_by: Optional[int] = None) -> None:
        """Mark message as read."""
        if self.status == MessageStatus.UNREAD:
            self.status = MessageStatus.READ
            self.read_at = datetime.utcnow()
            self.updated_by = read_by
    
    def archive(self, archived_by: Optional[int] = None) -> None:
        """Archive the message."""
        self.status = MessageStatus.ARCHIVED
        self.updated_by = archived_by