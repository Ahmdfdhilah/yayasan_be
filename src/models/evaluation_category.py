"""EvaluationCategory model for PKG System."""

from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .evaluation_aspect import EvaluationAspect


class EvaluationCategory(BaseModel, SQLModel, table=True):
    """Model for evaluation categories (e.g., Pedagogik, Kepribadian, Sosial, Profesional)."""
    
    __tablename__ = "evaluation_categories"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=100, nullable=False, unique=True, index=True)
    description: Optional[str] = Field(default=None)
    
    # Ordering
    display_order: int = Field(default=1, index=True)
    
    # Status
    is_active: bool = Field(default=True, index=True)
    
    # Relationships
    aspects: List["EvaluationAspect"] = Relationship(back_populates="category")
    
    def __repr__(self) -> str:
        return f"<EvaluationCategory(id={self.id}, name={self.name}, order={self.display_order})>"
    
    def activate(self) -> None:
        """Activate this evaluation category."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this evaluation category."""
        self.is_active = False