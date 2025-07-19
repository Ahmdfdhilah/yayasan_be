"""Evaluation Result schemas for PKG System API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal

from src.models.enums import EvaluationGrade
from src.schemas.shared import BaseListResponse
from src.schemas.filters import PaginationParams, SearchParams, DateRangeFilter


# ===== BASE SCHEMAS =====

class EvaluationResultBase(BaseModel):
    """Base evaluation result schema."""
    teacher_id: int = Field(..., description="Teacher user ID")
    evaluator_id: int = Field(..., description="Evaluator user ID")
    academic_year: str = Field(..., min_length=1, max_length=20, description="Academic year")
    semester: str = Field(..., min_length=1, max_length=20, description="Semester")
    total_score: int = Field(..., ge=0, description="Total score achieved")
    max_score: int = Field(..., ge=1, description="Maximum possible score")
    performance_value: Decimal = Field(..., ge=0, le=125, description="Performance value (with 1.25 multiplier)")
    grade_category: str = Field(..., max_length=50, description="Grade category")
    recommendations: Optional[str] = Field(None, description="Evaluation recommendations")
    
    @field_validator('academic_year')
    @classmethod
    def validate_academic_year(cls, year: str) -> str:
        """Validate academic year format."""
        return year.strip()
    
    @field_validator('semester')
    @classmethod
    def validate_semester(cls, semester: str) -> str:
        """Validate semester format."""
        return semester.strip()
    
    @field_validator('performance_value')
    @classmethod
    def validate_performance_value(cls, value: Decimal) -> Decimal:
        """Validate performance value is within bounds."""
        if value < 0 or value > 125:
            raise ValueError("Performance value must be between 0 and 125")
        return value


# ===== REQUEST SCHEMAS =====

class EvaluationResultCreate(EvaluationResultBase):
    """Schema for creating an evaluation result."""
    pass


class EvaluationResultUpdate(BaseModel):
    """Schema for updating an evaluation result."""
    total_score: Optional[int] = Field(None, ge=0)
    max_score: Optional[int] = Field(None, ge=1)
    recommendations: Optional[str] = None


class EvaluationResultCalculateFromEvaluations(BaseModel):
    """Schema for calculating result from individual evaluations."""
    teacher_id: int = Field(..., description="Teacher user ID")
    evaluator_id: int = Field(..., description="Evaluator user ID")
    academic_year: str = Field(..., description="Academic year")
    semester: str = Field(..., description="Semester")
    evaluation_ids: List[int] = Field(..., min_items=1, description="List of teacher evaluation IDs")
    recommendations: Optional[str] = None


# ===== RESPONSE SCHEMAS =====

class EvaluationResultResponse(BaseModel):
    """Schema for evaluation result response."""
    id: int
    teacher_id: int
    evaluator_id: int
    academic_year: str
    semester: str
    total_score: int
    max_score: int
    performance_value: Decimal
    grade_category: str
    recommendations: Optional[str] = None
    evaluation_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    academic_period: str = Field(..., description="Formatted academic period")
    score_percentage: Decimal = Field(..., description="Score as percentage")
    performance_percentage: Decimal = Field(..., description="Performance value as percentage")
    grade_description: str = Field(..., description="Detailed grade description")
    
    # Related data
    teacher_name: Optional[str] = Field(None, description="Teacher name")
    teacher_email: Optional[str] = Field(None, description="Teacher email")
    evaluator_name: Optional[str] = Field(None, description="Evaluator name")
    
    @classmethod
    def from_evaluation_result_model(cls, result, include_relations: bool = False) -> "EvaluationResultResponse":
        """Create EvaluationResultResponse from EvaluationResult model."""
        data = {
            "id": result.id,
            "teacher_id": result.teacher_id,
            "evaluator_id": result.evaluator_id,
            "academic_year": result.academic_year,
            "semester": result.semester,
            "total_score": result.total_score,
            "max_score": result.max_score,
            "performance_value": result.performance_value,
            "grade_category": result.grade_category,
            "recommendations": result.recommendations,
            "evaluation_date": result.evaluation_date,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
            "academic_period": result.academic_period,
            "score_percentage": result.score_percentage,
            "performance_percentage": result.performance_percentage,
            "grade_description": result.get_grade_description()
        }
        
        if include_relations:
            data.update({
                "teacher_name": result.teacher.display_name if hasattr(result, 'teacher') and result.teacher else None,
                "teacher_email": result.teacher.email if hasattr(result, 'teacher') and result.teacher else None,
                "evaluator_name": result.evaluator.display_name if hasattr(result, 'evaluator') and result.evaluator else None
            })
        
        return cls(**data)
    
    model_config = {"from_attributes": True}


class EvaluationResultListResponse(BaseListResponse[EvaluationResultResponse]):
    """Standardized evaluation result list response."""
    pass


class EvaluationResultSummary(BaseModel):
    """Schema for evaluation result summary (lighter response)."""
    id: int
    teacher_id: int
    academic_year: str
    semester: str
    performance_value: Decimal
    grade_category: str
    evaluation_date: datetime
    
    # Related data
    teacher_name: Optional[str] = None
    
    @classmethod
    def from_evaluation_result_model(cls, result) -> "EvaluationResultSummary":
        """Create EvaluationResultSummary from EvaluationResult model."""
        return cls(
            id=result.id,
            teacher_id=result.teacher_id,
            academic_year=result.academic_year,
            semester=result.semester,
            performance_value=result.performance_value,
            grade_category=result.grade_category,
            evaluation_date=result.evaluation_date,
            teacher_name=result.teacher.display_name if hasattr(result, 'teacher') and result.teacher else None
        )
    
    model_config = {"from_attributes": True}


# ===== FILTER SCHEMAS =====

class EvaluationResultFilterParams(PaginationParams, SearchParams, DateRangeFilter):
    """Filter parameters for evaluation result listing."""
    
    # Result-specific filters
    teacher_id: Optional[int] = Field(None, description="Filter by teacher ID")
    evaluator_id: Optional[int] = Field(None, description="Filter by evaluator ID")
    academic_year: Optional[str] = Field(None, description="Filter by academic year")
    semester: Optional[str] = Field(None, description="Filter by semester")
    grade_category: Optional[str] = Field(None, description="Filter by grade category")
    min_performance: Optional[Decimal] = Field(None, ge=0, description="Minimum performance value")
    max_performance: Optional[Decimal] = Field(None, le=125, description="Maximum performance value")
    min_score_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Minimum score percentage")
    has_recommendations: Optional[bool] = Field(None, description="Filter results with/without recommendations")
    
    # Date filters
    evaluated_after: Optional[datetime] = Field(None, description="Filter results after this date")
    evaluated_before: Optional[datetime] = Field(None, description="Filter results before this date")
    
    # Grade filters
    excellent_only: Optional[bool] = Field(None, description="Filter only excellent grades")
    needs_improvement_only: Optional[bool] = Field(None, description="Filter only grades needing improvement")
    
    # Override search field description
    q: Optional[str] = Field(None, description="Search in teacher name, evaluator name, or recommendations")
    
    # Override default sort
    sort_by: str = Field(default="evaluation_date", description="Sort field")


# ===== BULK OPERATIONS =====

class EvaluationResultBulkUpdate(BaseModel):
    """Schema for bulk evaluation result updates."""
    result_ids: List[int] = Field(..., min_items=1, description="List of result IDs to update")
    recommendations: Optional[str] = None


class EvaluationResultBulkRecalculate(BaseModel):
    """Schema for bulk recalculation of results."""
    result_ids: List[int] = Field(..., min_items=1, description="List of result IDs to recalculate")
    use_latest_evaluations: bool = Field(default=True, description="Use latest evaluation data")


# ===== COMPREHENSIVE REPORTS =====

class TeacherPerformanceComparison(BaseModel):
    """Schema for comparing teacher performance."""
    teacher_id: int
    teacher_name: str
    current_period: EvaluationResultSummary
    previous_period: Optional[EvaluationResultSummary] = None
    performance_change: Optional[Decimal] = Field(None, description="Performance change from previous period")
    trend: str = Field(description="Improvement, decline, or stable")
    rank_in_organization: Optional[int] = None
    percentile: Optional[Decimal] = None


class OrganizationPerformanceOverview(BaseModel):
    """Schema for organization-wide performance overview."""
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    academic_year: str
    semester: str
    total_teachers: int
    evaluated_teachers: int
    completion_rate: Decimal
    
    # Performance metrics
    avg_performance_value: Decimal
    median_performance_value: Decimal
    grade_distribution: Dict[str, int] = Field(description="Count of teachers per grade")
    
    # Comparative data
    top_performers: List[TeacherPerformanceComparison]
    bottom_performers: List[TeacherPerformanceComparison]
    most_improved: List[TeacherPerformanceComparison]
    most_declined: List[TeacherPerformanceComparison]


# ===== ANALYTICS SCHEMAS =====

class EvaluationResultAnalytics(BaseModel):
    """Schema for evaluation result analytics."""
    total_results: int
    unique_teachers: int
    unique_evaluators: int
    avg_performance_value: Decimal
    performance_distribution: Dict[str, int] = Field(description="Performance value distribution")
    grade_distribution: Dict[str, int] = Field(description="Grade category distribution")
    results_by_period: Dict[str, int] = Field(description="Results per academic period")
    score_trends: Dict[str, List[Decimal]] = Field(description="Score trends over time")
    improvement_rate: Decimal = Field(description="Overall system improvement rate")


class PerformanceTrendAnalysis(BaseModel):
    """Schema for performance trend analysis."""
    teacher_id: int
    teacher_name: str
    historical_results: List[EvaluationResultSummary]
    trend_direction: str = Field(description="Overall trend direction")
    trend_strength: Decimal = Field(description="Strength of trend (correlation coefficient)")
    projected_next_performance: Optional[Decimal] = Field(None, description="Projected next period performance")
    consistency_score: Decimal = Field(description="Performance consistency score")
    volatility: Decimal = Field(description="Performance volatility measure")


class SystemPerformanceReport(BaseModel):
    """Schema for comprehensive system performance report."""
    report_period: str = Field(description="Reporting period")
    generated_at: datetime
    
    # Overall analytics
    system_analytics: EvaluationResultAnalytics
    organization_overviews: List[OrganizationPerformanceOverview]
    
    # Trend analysis
    performance_trends: List[PerformanceTrendAnalysis]
    
    # Insights and recommendations
    key_insights: List[str] = Field(description="Key insights from the data")
    system_recommendations: List[str] = Field(description="Recommendations for system improvement")
    teacher_interventions: List[Dict[str, Any]] = Field(description="Recommended teacher interventions")
    
    # Quality metrics
    evaluation_quality_score: Decimal = Field(description="Overall evaluation quality score")
    data_completeness: Decimal = Field(description="Data completeness percentage")
    evaluator_consistency: Decimal = Field(description="Inter-evaluator consistency score")