"""Board member model for organization management."""

from typing import Optional
from sqlmodel import Field, SQLModel

from .base import BaseModel


class BoardMember(BaseModel, SQLModel, table=True):
    """Board member model for organization management."""
    
    __tablename__ = "board_members"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    position: str = Field(max_length=255, nullable=False, description="Position/title in the board")
    img_url: Optional[str] = Field(max_length=500, default=None, description="Profile image URL")
    description: Optional[str] = Field(default=None, description="Bio or description")
    display_order: int = Field(default=0, description="Order for display")
    
    def __repr__(self) -> str:
        return f"<BoardMember(id={self.id}, name={self.name}, position={self.position})>"
    
    @property
    def short_description(self) -> str:
        """Get shortened description."""
        if not self.description:
            return ""
        return (self.description[:100] + "...") if len(self.description) > 100 else self.description