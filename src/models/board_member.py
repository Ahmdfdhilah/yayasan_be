"""Board member model for organization management."""

from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import validator

from .base import BaseModel
from ..utils.sanitize_html import sanitize_html_content

if TYPE_CHECKING:
    from .board_group import BoardGroup


class BoardMember(BaseModel, SQLModel, table=True):
    """Board member model for organization management."""
    
    __tablename__ = "board_members"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    position: str = Field(max_length=255, nullable=False, description="Position/title in the board")
    group_id: Optional[int] = Field(default=None, foreign_key="board_groups.id", description="Board group ID")
    member_order: int = Field(default=1, description="Order within the group", index=True)
    img_url: Optional[str] = Field(max_length=500, default=None, description="Profile image URL")
    description: Optional[str] = Field(default=None, description="Bio or description")
    
    group: Optional["BoardGroup"] = Relationship(back_populates="members")
    
    def __repr__(self) -> str:
        return f"<BoardMember(id={self.id}, name={self.name}, position={self.position})>"
    
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