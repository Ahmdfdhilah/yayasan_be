"""Evaluation Aspect schemas for PKG System API endpoints - Simplified."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date

from src.schemas.shared import BaseListResponse
from typing import Optional
from pydantic import Field


# ===== BASE SCHEMAS =====

class EvaluationAspectBase(BaseModel):
    """Base evaluation aspect schema - simplified without weights and scores."""
    aspect_name: str = Field(..., min_length=1, max_length=255, description="Name of evaluation aspect")
    category: str = Field(..., min_length=1, max_length=100, description="Category of evaluation aspect")
    description: Optional[str] = Field(None, description="Detailed description of the aspect")
    is_active: bool = Field(default=True, description="Whether aspect is active")
    
    @field_validator('aspect_name')
    @classmethod
    def validate_aspect_name(cls, name: str) -> str:
        """Validate and normalize aspect name."""
        return name.strip()


# ===== REQUEST SCHEMAS =====

class EvaluationAspectCreate(EvaluationAspectBase):
    """Schema for creating an evaluation aspect."""
    pass


class EvaluationAspectUpdate(BaseModel):
    """Schema for updating an evaluation aspect."""
    aspect_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('aspect_name')
    @classmethod
    def validate_aspect_name(cls, name: Optional[str]) -> Optional[str]:
        """Validate and normalize aspect name if provided."""
        return name.strip() if name else None


class EvaluationAspectBulkCreate(BaseModel):
    """Schema for bulk creating evaluation aspects."""
    aspects: List[EvaluationAspectCreate] = Field(..., min_items=1, description="List of aspects to create")


# ===== RESPONSE SCHEMAS =====

class EvaluationAspectResponse(BaseModel):
    """Schema for evaluation aspect response - simplified."""
    id: int
    aspect_name: str
    category: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Statistics
    evaluation_count: int = Field(default=0, description="Number of evaluations using this aspect")
    
    @classmethod
    def from_evaluation_aspect_model(cls, aspect, include_stats: bool = False) -> "EvaluationAspectResponse":
        """Create EvaluationAspectResponse from EvaluationAspect model."""
        data = {
            "id": aspect.id,
            "aspect_name": aspect.aspect_name,
            "category": aspect.category,
            "description": aspect.description,
            "is_active": aspect.is_active,
            "created_at": aspect.created_at,
            "updated_at": aspect.updated_at,
        }
        
        if include_stats:
            # These would be calculated in the repository/service layer
            data.update({
                "evaluation_count": getattr(aspect, 'evaluation_count', 0),
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class EvaluationAspectListResponse(BaseListResponse[EvaluationAspectResponse]):
    """Standardized evaluation aspect list response."""
    pass


class EvaluationAspectSummary(BaseModel):
    """Schema for evaluation aspect summary (lighter response)."""
    id: int
    aspect_name: str
    category: str
    is_active: bool
    created_at: datetime
    
    # Statistics
    evaluation_count: int = Field(default=0)
    
    @classmethod
    def from_evaluation_aspect_model(cls, aspect) -> "EvaluationAspectSummary":
        """Create EvaluationAspectSummary from EvaluationAspect model."""
        return cls(
            id=aspect.id,
            aspect_name=aspect.aspect_name,
            category=aspect.category,
            is_active=aspect.is_active,
            created_at=aspect.created_at,
            evaluation_count=getattr(aspect, 'evaluation_count', 0)
        )
    
    model_config = {"from_attributes": True}


# ===== BASE FILTER SCHEMAS =====

class PaginationParams(BaseModel):
    """Base pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")


class SearchParams(BaseModel):
    """Base search parameters."""
    
    q: Optional[str] = Field(default=None, description="Search query")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


# ===== FILTER SCHEMAS =====

class EvaluationAspectFilterParams(PaginationParams, SearchParams):
    """Filter parameters for evaluation aspect listing."""
    
    # Aspect-specific filters
    category: Optional[str] = Field(None, description="Filter by category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_evaluations: Optional[bool] = Field(None, description="Filter aspects with/without evaluations")
    
    # Date filtering for creation date
    created_after: Optional[date] = Field(None, description="Filter aspects created after this date")
    created_before: Optional[date] = Field(None, description="Filter aspects created before this date")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in aspect name, description, or category")
    
    # Override default sort
    sort_by: str = Field(default="aspect_name", description="Sort field (aspect_name, category, is_active, created_at, updated_at)")


# ===== BULK OPERATIONS =====

class EvaluationAspectBulkUpdate(BaseModel):
    """Schema for bulk evaluation aspect updates."""
    aspect_ids: List[int] = Field(..., min_items=1, description="List of aspect IDs to update")
    is_active: Optional[bool] = None


class EvaluationAspectBulkDelete(BaseModel):
    """Schema for bulk evaluation aspect deletion."""
    aspect_ids: List[int] = Field(..., min_items=1, description="List of aspect IDs to delete")
    force_delete: bool = Field(default=False, description="Force delete even if aspect has evaluations")


# ===== ANALYTICS SCHEMAS =====

class EvaluationAspectAnalytics(BaseModel):
    """Schema for evaluation aspect analytics - simplified."""
    total_aspects: int
    active_aspects: int
    inactive_aspects: int
    most_used_aspects: List[Dict[str, Any]] = Field(description="Most frequently evaluated aspects")
    least_used_aspects: List[Dict[str, Any]] = Field(description="Least frequently evaluated aspects")
    avg_grade_by_aspect: Dict[str, str] = Field(description="Average grades per aspect")


class AspectPerformanceAnalysis(BaseModel):
    """Schema for aspect performance analysis - simplified."""
    aspect_id: int
    aspect_name: str
    total_evaluations: int
    avg_grade: str = Field(description="Average grade (A, B, C, D)")
    grade_distribution: Dict[str, int] = Field(description="Grade distribution (A, B, C, D)")
    trend_data: List[Dict[str, Any]] = Field(description="Performance trend over time")
    top_performers: List[Dict[str, Any]] = Field(description="Top performing teachers in this aspect")
    improvement_needed: List[Dict[str, Any]] = Field(description="Teachers needing improvement")


class EvaluationAspectStats(BaseModel):
    """Schema for comprehensive evaluation aspect statistics - simplified."""
    summary: EvaluationAspectAnalytics
    aspect_performance: List[AspectPerformanceAnalysis]
    usage_trends: Dict[str, List[int]] = Field(description="Usage trends over time")
    recommendations: List[str] = Field(description="System recommendations for aspect management")