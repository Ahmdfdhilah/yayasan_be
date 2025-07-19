"""Evaluation Aspect schemas for PKG System API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal

from src.schemas.shared import BaseListResponse
from src.schemas.filters import PaginationParams, SearchParams, DateRangeFilter


# ===== BASE SCHEMAS =====

class EvaluationAspectBase(BaseModel):
    """Base evaluation aspect schema (Universal across all organizations)."""
    aspect_name: str = Field(..., min_length=1, max_length=200, description="Name of evaluation aspect")
    category: str = Field(..., min_length=1, max_length=100, description="Category of evaluation aspect")
    description: Optional[str] = Field(None, description="Detailed description of the aspect")
    max_score: int = Field(..., ge=1, le=100, description="Maximum possible score")
    weight: Decimal = Field(..., ge=0, le=100, description="Weight percentage for this aspect")
    is_active: bool = Field(default=True, description="Whether aspect is active")
    
    @field_validator('aspect_name')
    @classmethod
    def validate_aspect_name(cls, name: str) -> str:
        """Validate and normalize aspect name."""
        return name.strip()
    
    @field_validator('weight')
    @classmethod
    def validate_weight(cls, weight: Decimal) -> Decimal:
        """Validate weight is a proper decimal."""
        if weight < 0 or weight > 100:
            raise ValueError("Weight must be between 0 and 100")
        return weight


# ===== REQUEST SCHEMAS =====

class EvaluationAspectCreate(EvaluationAspectBase):
    """Schema for creating an evaluation aspect."""
    pass


class EvaluationAspectUpdate(BaseModel):
    """Schema for updating an evaluation aspect."""
    aspect_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    max_score: Optional[int] = Field(None, ge=1, le=100)
    weight: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    
    @field_validator('aspect_name')
    @classmethod
    def validate_aspect_name(cls, name: Optional[str]) -> Optional[str]:
        """Validate and normalize aspect name if provided."""
        return name.strip() if name else None
    
    @field_validator('weight')
    @classmethod
    def validate_weight(cls, weight: Optional[Decimal]) -> Optional[Decimal]:
        """Validate weight if provided."""
        if weight is not None and (weight < 0 or weight > 100):
            raise ValueError("Weight must be between 0 and 100")
        return weight


class EvaluationAspectBulkCreate(BaseModel):
    """Schema for bulk creating evaluation aspects."""
    aspects: List[EvaluationAspectCreate] = Field(..., min_items=1, description="List of aspects to create")


# ===== RESPONSE SCHEMAS =====

class EvaluationAspectResponse(BaseModel):
    """Schema for evaluation aspect response."""
    id: int
    aspect_name: str
    category: str
    description: Optional[str] = None
    max_score: int
    weight: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    weight_percentage: str = Field(..., description="Weight as formatted percentage")
    
    # Statistics
    evaluation_count: int = Field(default=0, description="Number of evaluations using this aspect")
    avg_score: Optional[Decimal] = Field(None, description="Average score across all evaluations")
    
    @classmethod
    def from_evaluation_aspect_model(cls, aspect, include_stats: bool = False) -> "EvaluationAspectResponse":
        """Create EvaluationAspectResponse from EvaluationAspect model."""
        data = {
            "id": aspect.id,
            "aspect_name": aspect.aspect_name,
            "category": aspect.category,
            "description": aspect.description,
            "max_score": aspect.max_score,
            "weight": aspect.weight,
            "is_active": aspect.is_active,
            "created_at": aspect.created_at,
            "updated_at": aspect.updated_at,
            "weight_percentage": f"{aspect.weight}%"
        }
        
        if include_stats:
            # These would be calculated in the repository/service layer
            data.update({
                "evaluation_count": getattr(aspect, 'evaluation_count', 0),
                "avg_score": getattr(aspect, 'avg_score', None)
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
    max_score: int
    weight: Decimal
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
            max_score=aspect.max_score,
            weight=aspect.weight,
            is_active=aspect.is_active,
            created_at=aspect.created_at,
            evaluation_count=getattr(aspect, 'evaluation_count', 0)
        )
    
    model_config = {"from_attributes": True}


# ===== FILTER SCHEMAS =====

class EvaluationAspectFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for evaluation aspect listing."""
    
    # Aspect-specific filters
    category: Optional[str] = Field(None, description="Filter by category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    min_weight: Optional[Decimal] = Field(None, ge=0, description="Minimum weight percentage")
    max_weight: Optional[Decimal] = Field(None, le=100, description="Maximum weight percentage")
    min_score: Optional[int] = Field(None, ge=1, description="Minimum max score")
    max_score: Optional[int] = Field(None, le=100, description="Maximum max score")
    has_evaluations: Optional[bool] = Field(None, description="Filter aspects with/without evaluations")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in aspect name or description")
    
    # Override default sort
    sort_by: str = Field(default="aspect_name", description="Sort field")


# ===== BULK OPERATIONS =====

class EvaluationAspectBulkUpdate(BaseModel):
    """Schema for bulk evaluation aspect updates."""
    aspect_ids: List[int] = Field(..., min_items=1, description="List of aspect IDs to update")
    is_active: Optional[bool] = None


class EvaluationAspectBulkDelete(BaseModel):
    """Schema for bulk evaluation aspect deletion."""
    aspect_ids: List[int] = Field(..., min_items=1, description="List of aspect IDs to delete")
    force_delete: bool = Field(default=False, description="Force delete even if aspect has evaluations")


class WeightValidation(BaseModel):
    """Schema for validating aspect weights."""
    aspect_weights: Dict[int, Decimal] = Field(..., description="Aspect ID to weight mapping")


class WeightValidationResponse(BaseModel):
    """Schema for weight validation response."""
    is_valid: bool
    total_weight: Decimal
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ===== ANALYTICS SCHEMAS =====

class EvaluationAspectAnalytics(BaseModel):
    """Schema for evaluation aspect analytics."""
    total_aspects: int
    active_aspects: int
    inactive_aspects: int
    total_weight: Decimal = Field(description="Sum of all active aspect weights")
    weight_distribution: Dict[str, Decimal] = Field(description="Weight distribution across aspects")
    most_used_aspects: List[Dict[str, Any]] = Field(description="Most frequently evaluated aspects")
    least_used_aspects: List[Dict[str, Any]] = Field(description="Least frequently evaluated aspects")
    avg_score_by_aspect: Dict[str, Decimal] = Field(description="Average scores per aspect")


class AspectPerformanceAnalysis(BaseModel):
    """Schema for aspect performance analysis."""
    aspect_id: int
    aspect_name: str
    total_evaluations: int
    avg_score: Decimal
    min_score: int
    max_score: int
    score_distribution: Dict[str, int] = Field(description="Score distribution histogram")
    trend_data: List[Dict[str, Any]] = Field(description="Performance trend over time")
    top_performers: List[Dict[str, Any]] = Field(description="Top performing teachers in this aspect")
    improvement_needed: List[Dict[str, Any]] = Field(description="Teachers needing improvement")


class EvaluationAspectStats(BaseModel):
    """Schema for comprehensive evaluation aspect statistics."""
    summary: EvaluationAspectAnalytics
    aspect_performance: List[AspectPerformanceAnalysis]
    weight_balance_check: WeightValidationResponse
    usage_trends: Dict[str, List[int]] = Field(description="Usage trends over time")
    recommendations: List[str] = Field(description="System recommendations for aspect management")