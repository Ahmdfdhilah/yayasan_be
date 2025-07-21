"""Evaluation Aspect model for PKG System - Simplified."""

from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .teacher_evaluation_item import TeacherEvaluationItem
    from .evaluation_category import EvaluationCategory


class EvaluationAspect(BaseModel, SQLModel, table=True):
    """Simplified evaluation aspect model for teacher performance assessments."""
    
    __tablename__ = "evaluation_aspects"
    
    id: int = Field(primary_key=True)
    aspect_name: str = Field(max_length=255, nullable=False, index=True)
    description: Optional[str] = Field(default=None)
    
    # Foreign Key to EvaluationCategory
    category_id: int = Field(foreign_key="evaluation_categories.id", index=True)
    
    # Ordering within category
    display_order: int = Field(default=1, index=True)
    
    # Status (Universal - no organization filtering)
    is_active: bool = Field(default=True, index=True)
    
    # Relationships
    category: "EvaluationCategory" = Relationship(back_populates="aspects")
    teacher_evaluation_items: List["TeacherEvaluationItem"] = Relationship(back_populates="aspect")
    
    def __repr__(self) -> str:
        return f"<EvaluationAspect(id={self.id}, name={self.aspect_name}, category_id={self.category_id})>"
    
    def activate(self) -> None:
        """Activate this evaluation aspect."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this evaluation aspect."""
        self.is_active = False