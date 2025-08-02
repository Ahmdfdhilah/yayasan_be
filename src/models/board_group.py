"""Board group model for organizing board members."""

from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .board_member import BoardMember


class BoardGroup(BaseModel, SQLModel, table=True):
    """Board group model for organizing board members hierarchically."""
    
    __tablename__ = "board_groups"
    
    id: int = Field(primary_key=True)
    title: str = Field(max_length=255, nullable=False, description="Group title (e.g., 'Pengurus Inti', 'Jajaran Dewan')")
    display_order: int = Field(description="Display order (1=first, 2=second, etc.)", unique=True)
    description: Optional[str] = Field(default=None, description="Group description")
    
    members: List["BoardMember"] = Relationship(back_populates="group")
    
    def __repr__(self) -> str:
        return f"<BoardGroup(id={self.id}, title={self.title}, display_order={self.display_order})>"