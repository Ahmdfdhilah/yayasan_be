"""Program model for educational programs management."""

from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import validator

from .base import BaseModel
from ..utils.sanitize_html import sanitize_html_content


class Program(BaseModel, SQLModel, table=True):
    """Program model for managing educational programs."""
    
    __tablename__ = "programs"
    
    id: int = Field(primary_key=True)
    title: str = Field(max_length=255, nullable=False, index=True, description="Program title")
    excerpt: Optional[str] = Field(max_length=500, default=None, description="Short program summary")
    description: Optional[str] = Field(default=None, description="Full program description (HTML)")
    img_url: Optional[str] = Field(max_length=500, default=None, description="Program image URL")
    
    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize HTML content in description field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    def __repr__(self) -> str:
        return f"<Program(id={self.id}, title={self.title})>"