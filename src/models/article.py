"""Article model for blog posts and content."""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from pydantic import validator

from .base import BaseModel
from ..utils.sanitize_html import sanitize_html_content


class Article(BaseModel, SQLModel, table=True):
    """Article model for blog posts and content."""
    
    __tablename__ = "articles"
    
    id: int = Field(primary_key=True)
    title: str = Field(max_length=255, nullable=False, index=True)
    description: str = Field(nullable=False, description="Full article HTML content")
    slug: str = Field(max_length=255, unique=True, nullable=False, index=True)
    excerpt: Optional[str] = Field(max_length=500, default=None, description="Short summary")
    img_url: Optional[str] = Field(max_length=500, default=None, description="Article image URL")
    published_at: Optional[datetime] = Field(default=None, description="Publication date")
    category: str = Field(max_length=100, nullable=False, index=True, description="Article category")
    is_published: bool = Field(default=False, description="Publication status")
    
    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title={self.title}, slug={self.slug})>"
    
    @property
    def is_draft(self) -> bool:
        """Check if article is a draft."""
        return not self.is_published or self.published_at is None
    
    def publish(self) -> None:
        """Publish the article."""
        self.is_published = True
        if self.published_at is None:
            self.published_at = datetime.utcnow()
    
    def unpublish(self) -> None:
        """Unpublish the article."""
        self.is_published = False
    
    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize HTML content in description field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    def get_excerpt(self, length: int = 150) -> str:
        """Get excerpt or truncated description."""
        if self.excerpt:
            return self.excerpt
        if self.description:
            return (self.description[:length] + "...") if len(self.description) > length else self.description
        return ""