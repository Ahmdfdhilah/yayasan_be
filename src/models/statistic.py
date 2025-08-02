"""Statistic model for displaying statistics data."""

from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import validator

from .base import BaseModel
from ..utils.sanitize_html import sanitize_html_content


class Statistic(BaseModel, SQLModel, table=True):
    """Statistic model for displaying statistics data."""
    
    __tablename__ = "statistics"
    
    id: int = Field(primary_key=True)
    title: str = Field(max_length=255, nullable=False, index=True, description="Statistic title")
    description: Optional[str] = Field(default=None, description="Statistic description")
    stats: str = Field(max_length=255, nullable=False, description="Statistics value with suffix (e.g., '20%', '20km', '20')")
    img_url: Optional[str] = Field(max_length=500, default=None, description="Icon image URL")
    display_order: int = Field(default=1, description="Display order for sorting", index=True)
    
    def __repr__(self) -> str:
        return f"<Statistic(id={self.id}, title={self.title}, stats={self.stats})>"
    
    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize HTML content in description field."""
        if v:
            return sanitize_html_content(v)
        return v
    
    @property
    def short_description(self) -> str:
        """Get shortened description."""
        if not self.description:
            return ""
        return (self.description[:100] + "...") if len(self.description) > 100 else self.description
    
    @property
    def display_name(self) -> str:
        """Get display name for the statistic."""
        return f"{self.title}: {self.stats}"