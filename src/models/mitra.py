"""Mitra model for partnership management."""

from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import validator

from .base import BaseModel
from ..utils.sanitize_html import sanitize_html_content


class Mitra(BaseModel, SQLModel, table=True):
    """Mitra model for managing business partnerships."""
    
    __tablename__ = "mitras"
    
    id: int = Field(primary_key=True)
    title: str = Field(max_length=255, nullable=False, index=True, description="Partnership title")
    description: Optional[str] = Field(default=None, description="Partnership description (HTML)")
    img_url: Optional[str] = Field(max_length=500, default=None, description="Partnership image URL")
    
    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize HTML content in description field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    def __repr__(self) -> str:
        return f"<Mitra(id={self.id}, title={self.title})>"