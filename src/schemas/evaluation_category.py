"""EvaluationCategory schemas for PKG System API endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from src.schemas.shared import BaseListResponse


# ===== BASE SCHEMAS =====

class EvaluationCategoryBase(BaseModel):
    """Base evaluation category schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    display_order: int = Field(default=1, ge=1, description="Display order")
    is_active: bool = Field(default=True, description="Whether category is active")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate and normalize category name."""
        return name.strip()


# ===== REQUEST SCHEMAS =====

class EvaluationCategoryCreate(EvaluationCategoryBase):
    """Schema for creating an evaluation category."""
    pass


class EvaluationCategoryUpdate(BaseModel):
    """Schema for updating an evaluation category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: Optional[str]) -> Optional[str]:
        """Validate and normalize category name if provided."""
        return name.strip() if name else None


# ===== RESPONSE SCHEMAS =====

class EvaluationCategoryResponse(BaseModel):
    """Schema for evaluation category response."""
    id: int
    name: str
    description: Optional[str] = None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Statistics
    aspects_count: int = Field(default=0, description="Number of aspects in this category")
    active_aspects_count: int = Field(default=0, description="Number of active aspects in this category")
    
    @classmethod
    def from_evaluation_category_model(cls, category, include_stats: bool = False) -> "EvaluationCategoryResponse":
        """Create EvaluationCategoryResponse from EvaluationCategory model."""
        data = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "display_order": category.display_order,
            "is_active": category.is_active,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
        }
        
        if include_stats:
            data.update({
                "aspects_count": getattr(category, 'aspects_count', 0),
                "active_aspects_count": getattr(category, 'active_aspects_count', 0),
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class EvaluationCategoryListResponse(BaseListResponse[EvaluationCategoryResponse]):
    """Standardized evaluation category list response."""
    pass


class EvaluationCategorySummary(BaseModel):
    """Schema for evaluation category summary (lighter response)."""
    id: int
    name: str
    display_order: int
    is_active: bool
    aspects_count: int = Field(default=0)
    
    @classmethod
    def from_evaluation_category_model(cls, category) -> "EvaluationCategorySummary":
        """Create EvaluationCategorySummary from EvaluationCategory model."""
        return cls(
            id=category.id,
            name=category.name,
            display_order=category.display_order,
            is_active=category.is_active,
            aspects_count=getattr(category, 'aspects_count', 0)
        )
    
    model_config = {"from_attributes": True}


# ===== ORDERING SCHEMAS =====

class CategoryOrderUpdate(BaseModel):
    """Schema for updating category display order."""
    category_id: int = Field(..., ge=1, description="Category ID")
    new_order: int = Field(..., ge=1, description="New display order")


class CategoriesReorder(BaseModel):
    """Schema for reordering multiple categories."""
    category_orders: dict[int, int] = Field(..., description="Mapping of category_id to new_order")


# ===== FILTER SCHEMAS =====

class EvaluationCategoryFilterParams(BaseModel):
    """Filter parameters for evaluation category listing."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    q: Optional[str] = Field(None, description="Search in category name or description")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    sort_by: str = Field(default="display_order", description="Sort field (name, display_order, is_active, created_at)")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


# ===== BULK OPERATIONS =====

class EvaluationCategoryBulkUpdate(BaseModel):
    """Schema for bulk category updates."""
    category_ids: List[int] = Field(..., min_items=1, description="List of category IDs to update")
    is_active: Optional[bool] = None


class EvaluationCategoryBulkDelete(BaseModel):
    """Schema for bulk category deletion."""
    category_ids: List[int] = Field(..., min_items=1, description="List of category IDs to delete")
    force_delete: bool = Field(default=False, description="Force delete even if category has aspects")