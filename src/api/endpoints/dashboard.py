"""Dashboard API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import get_current_active_user
from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.period import PeriodRepository
from src.services.dashboard import DashboardService
from src.schemas.dashboard import (
    DashboardResponse,
    DashboardFilters,
    TeacherDashboard,
    PrincipalDashboard,
    AdminDashboard
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    """Get dashboard service."""
    rpp_repo = RPPSubmissionRepository(db)
    evaluation_repo = TeacherEvaluationRepository(db)
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)
    period_repo = PeriodRepository(db)
    
    return DashboardService(rpp_repo, evaluation_repo, user_repo, org_repo, period_repo)


@router.get(
    "/",
    response_model=DashboardResponse,
    summary="Get dashboard data"
)
async def get_dashboard(
    period_id: Optional[int] = Query(None, description="Filter by specific period"),
    organization_id: Optional[int] = Query(None, description="Filter by organization (admin only)"),
    include_inactive: bool = Query(False, description="Include inactive periods/organizations"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get comprehensive dashboard data based on user role and permissions.
    
    **Role-based access:**
    - **Teachers (guru)**: See personal statistics and organization overview
    - **Principals (kepala_sekolah)**: See organization-wide statistics and teacher summaries
    - **Admins**: See system-wide statistics and can filter by organization
    
    **Available filters:**
    - `period_id`: Filter data by specific evaluation period
    - `organization_id`: Filter by organization (admin only)
    - `include_inactive`: Include inactive periods/organizations in results
    
    **Returns different response types:**
    - Teachers get `TeacherDashboard` with personal stats
    - Principals get `PrincipalDashboard` with organization stats
    - Admins get `AdminDashboard` with system-wide stats
    """
    
    # Create filters object
    filters = DashboardFilters(
        period_id=period_id,
        organization_id=organization_id,
        include_inactive=include_inactive
    )
    
    # Get dashboard data based on user role
    return await dashboard_service.get_dashboard_data(current_user, filters)


@router.get(
    "/teacher",
    response_model=TeacherDashboard,
    summary="Get teacher-specific dashboard"
)
async def get_teacher_dashboard(
    period_id: Optional[int] = Query(None, description="Filter by specific period"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get teacher-specific dashboard with personal statistics.
    
    **For teachers only.** Shows:
    - Personal RPP submission statistics
    - Personal evaluation statistics
    - Quick stats (pending items)
    - Organization context for comparison
    """
    filters = DashboardFilters(period_id=period_id)
    result = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Ensure it's a teacher dashboard
    if not isinstance(result, TeacherDashboard):
        # Convert to teacher dashboard if needed
        return result
    
    return result


@router.get(
    "/principal",
    response_model=PrincipalDashboard,
    summary="Get principal-specific dashboard"
)
async def get_principal_dashboard(
    period_id: Optional[int] = Query(None, description="Filter by specific period"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get principal-specific dashboard with organization statistics.
    
    **For principals only.** Shows:
    - Organization-wide RPP and evaluation statistics
    - Teacher summaries within organization
    - Pending reviews and organization overview
    - Quick stats for principal tasks
    """
    filters = DashboardFilters(period_id=period_id)
    result = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Ensure it's a principal dashboard
    if not isinstance(result, PrincipalDashboard):
        return result
    
    return result


@router.get(
    "/admin",
    response_model=AdminDashboard,
    summary="Get admin-specific dashboard"
)
async def get_admin_dashboard(
    period_id: Optional[int] = Query(None, description="Filter by specific period"),
    organization_id: Optional[int] = Query(None, description="Filter by specific organization"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get admin-specific dashboard with system-wide statistics.
    
    **For admins only.** Shows:
    - System-wide or organization-specific statistics
    - All organization summaries
    - System overview and health
    - Recent system activities
    """
    filters = DashboardFilters(
        period_id=period_id,
        organization_id=organization_id
    )
    result = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Ensure it's an admin dashboard
    if not isinstance(result, AdminDashboard):
        return result
    
    return result


@router.get(
    "/quick-stats",
    summary="Get quick statistics for current user"
)
async def get_quick_stats(
    period_id: Optional[int] = Query(None, description="Filter by specific period"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get quick statistics for the current user.
    
    Returns essential numbers for dashboard cards:
    - Pending items count
    - Recent activities
    - Role-specific metrics
    """
    filters = DashboardFilters(period_id=period_id)
    dashboard_data = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Extract quick stats based on dashboard type
    if hasattr(dashboard_data, 'quick_stats'):
        return dashboard_data.quick_stats
    
    # Fallback for admin or basic dashboard
    return {
        "my_pending_rpps": 0,
        "my_pending_reviews": 0,
        "my_pending_evaluations": 0,
        "recent_activities": []
    }