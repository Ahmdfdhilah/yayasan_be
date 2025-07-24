"""Gallery model for image management."""

from typing import Optional
from sqlmodel import Field, SQLModel

from .base import BaseModel


class Gallery(BaseModel, SQLModel, table=True):
    """Gallery model for image management."""
    
    __tablename__ = "galleries"
    
    id: int = Field(primary_key=True)
    img_url: str = Field(max_length=500, nullable=False, description="Image URL")
    title: str = Field(max_length=255, nullable=False, index=True, description="Image title")
    excerpt: Optional[str] = Field(max_length=500, default=None, description="Short description")
    display_order: int = Field(default=0, description="Order for display", index=True)
    
    def __repr__(self) -> str:
        return f"<Gallery(id={self.id}, title={self.title}, display_order={self.display_order})>"
    
    @property
    def short_excerpt(self) -> str:
        """Get shortened excerpt."""
        if not self.excerpt:
            return ""
        return (self.excerpt[:50] + "...") if len(self.excerpt) > 50 else self.excerpt