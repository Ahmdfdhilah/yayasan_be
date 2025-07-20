"""Dashboard API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
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
    period_id: int = Query(..., description="Period ID (required)"),
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
    
    **Required parameters:**
    - `period_id`: Evaluation period ID (required for all dashboard data)
    
    **Optional filters:**
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
    period_id: int = Query(..., description="Period ID (required)"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get teacher-specific dashboard with personal statistics.
    
    **For teachers only.** Shows:
    - Personal RPP submission statistics for the specified period
    - Personal evaluation statistics for the specified period
    - Quick stats (pending items)
    - Organization context for comparison
    
    **Required:** period_id - Evaluation period to filter data
    """
    filters = DashboardFilters(period_id=period_id)
    result = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Check if user is actually a teacher, if not return 403 Forbidden
    if not isinstance(result, TeacherDashboard):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is only available for teachers (guru)."
        )
    
    return result


@router.get(
    "/principal",
    response_model=PrincipalDashboard,
    summary="Get principal-specific dashboard"
)
async def get_principal_dashboard(
    period_id: int = Query(..., description="Period ID (required)"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get principal-specific dashboard with organization statistics.
    
    **For principals only.** Shows:
    - Organization-wide RPP and evaluation statistics for the specified period
    - Teacher summaries within organization for the specified period
    - Pending reviews and organization overview
    - Quick stats for principal tasks
    
    **Required:** period_id - Evaluation period to filter data
    """
    filters = DashboardFilters(period_id=period_id)
    
    # Validate that user has principal role before allowing access
    result = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Check if user is actually a principal, if not return 403 Forbidden
    if not isinstance(result, PrincipalDashboard):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is only available for principals (kepala_sekolah)."
        )
    
    return result


@router.get(
    "/admin",
    response_model=AdminDashboard,
    summary="Get admin-specific dashboard"
)
async def get_admin_dashboard(
    period_id: int = Query(..., description="Period ID (required)"),
    organization_id: Optional[int] = Query(None, description="Filter by specific organization"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get admin-specific dashboard with system-wide statistics.
    
    **For admins only.** Shows:
    - System-wide or organization-specific statistics for the specified period
    - All organization summaries for the specified period
    - System overview and health
    - Recent system activities
    
    **Required:** period_id - Evaluation period to filter data
    **Optional:** organization_id - Filter to specific organization
    """
    filters = DashboardFilters(
        period_id=period_id,
        organization_id=organization_id
    )
    result = await dashboard_service.get_dashboard_data(current_user, filters)
    
    # Check if user is actually an admin, if not return 403 Forbidden
    if not isinstance(result, AdminDashboard):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is only available for administrators (admin)."
        )
    
    return result


@router.get(
    "/quick-stats",
    summary="Get quick statistics for current user"
)
async def get_quick_stats(
    period_id: int = Query(..., description="Period ID (required)"),
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