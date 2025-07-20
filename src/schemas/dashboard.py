"""Dashboard schemas for PKG system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RPPDashboardStats(BaseModel):
    """RPP submission statistics for dashboard."""
    total_submissions: int = Field(description="Total number of RPP submissions")
    pending_submissions: int = Field(description="Number of pending submissions")
    approved_submissions: int = Field(description="Number of approved submissions")
    rejected_submissions: int = Field(description="Number of rejected submissions")
    pending_reviews: int = Field(description="Number of submissions pending review")
    avg_review_time_hours: Optional[float] = Field(description="Average review time in hours")
    submission_rate: float = Field(description="Submission completion rate percentage")
    

class TeacherEvaluationDashboardStats(BaseModel):
    """Teacher evaluation statistics for dashboard."""
    total_evaluations: int = Field(description="Total number of evaluations")
    completed_evaluations: int = Field(description="Number of completed evaluations")
    pending_evaluations: int = Field(description="Number of pending evaluations")
    completion_rate: float = Field(description="Evaluation completion rate percentage")
    avg_score: Optional[float] = Field(description="Average evaluation score")
    grade_distribution: Dict[str, int] = Field(description="Distribution of grades (A, B, C, D)")
    total_teachers: int = Field(description="Total number of teachers being evaluated")
    total_aspects: int = Field(description="Total number of evaluation aspects")


class OrganizationSummary(BaseModel):
    """Organization summary for admin dashboard."""
    organization_id: int = Field(description="Organization ID")
    organization_name: str = Field(description="Organization name")
    total_teachers: int = Field(description="Number of teachers in organization")
    rpp_stats: RPPDashboardStats = Field(description="RPP statistics for this organization")
    evaluation_stats: TeacherEvaluationDashboardStats = Field(description="Evaluation statistics for this organization")


class PeriodSummary(BaseModel):
    """Period summary information."""
    period_id: int = Field(description="Period ID")
    period_name: str = Field(description="Period name")
    start_date: Optional[datetime] = Field(description="Period start date")
    end_date: Optional[datetime] = Field(description="Period end date")
    is_active: bool = Field(description="Whether the period is currently active")


class DashboardResponse(BaseModel):
    """Main dashboard response containing all statistics."""
    period: Optional[PeriodSummary] = Field(description="Current period information")
    rpp_stats: RPPDashboardStats = Field(description="RPP submission statistics")
    evaluation_stats: TeacherEvaluationDashboardStats = Field(description="Teacher evaluation statistics")
    organizations: Optional[List[OrganizationSummary]] = Field(description="Organization-specific stats (admin only)")
    user_role: str = Field(description="Current user's role")
    organization_name: Optional[str] = Field(description="Current user's organization name")
    last_updated: datetime = Field(description="When the dashboard data was last updated")


class DashboardFilters(BaseModel):
    """Filters for dashboard data."""
    period_id: Optional[int] = Field(None, description="Filter by specific period")
    organization_id: Optional[int] = Field(None, description="Filter by organization (admin only)")
    include_inactive: bool = Field(False, description="Include inactive periods/organizations")


# Quick stats for summary cards
class QuickStats(BaseModel):
    """Quick statistics for dashboard cards."""
    my_pending_rpps: int = Field(description="Number of user's pending RPP submissions")
    my_pending_reviews: int = Field(description="Number of RPP reviews pending for user")
    my_pending_evaluations: int = Field(description="Number of pending evaluations for user")
    recent_activities: List[Dict[str, Any]] = Field(description="Recent activities for the user")


class TeacherDashboard(DashboardResponse):
    """Teacher-specific dashboard with personal statistics."""
    quick_stats: QuickStats = Field(description="Quick personal statistics")
    my_rpp_stats: RPPDashboardStats = Field(description="Personal RPP submission statistics")
    my_evaluation_stats: TeacherEvaluationDashboardStats = Field(description="Personal evaluation statistics")


class PrincipalDashboard(DashboardResponse):
    """Principal-specific dashboard with organization statistics."""
    quick_stats: QuickStats = Field(description="Quick statistics for principal")
    organization_overview: Dict[str, Any] = Field(description="Detailed organization overview")
    teacher_summaries: List[Dict[str, Any]] = Field(description="Summary of teachers in organization")


class AdminDashboard(DashboardResponse):
    """Admin-specific dashboard with system-wide statistics."""
    system_overview: Dict[str, Any] = Field(description="System-wide overview statistics")
    organization_summaries: List[OrganizationSummary] = Field(description="All organizations summary")
    recent_system_activities: List[Dict[str, Any]] = Field(description="Recent system-wide activities")