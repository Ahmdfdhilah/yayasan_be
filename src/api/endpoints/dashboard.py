"""Dashboard API endpoints for PKG system overview."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.auth.permissions import get_current_active_user
from src.services.dashboard import DashboardService
from src.repositories.rpp_submission import RPPSubmissionRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.repositories.evaluation_result import EvaluationResultRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.schemas.dashboard import (
    DashboardOverview,
    UserDashboard,
    OrganizationDashboard,
    AdminDashboard
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    """Get dashboard service."""
    rpp_repo = RPPSubmissionRepository(db)
    evaluation_repo = TeacherEvaluationRepository(db)
    result_repo = EvaluationResultRepository(db)
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)
    
    return DashboardService(
        rpp_repo, evaluation_repo, result_repo, user_repo, org_repo
    )


@router.get(
    "/overview",
    response_model=DashboardOverview,
    summary="Get dashboard overview"
)
async def get_dashboard_overview(
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get comprehensive dashboard overview for current user."""
    user_roles = current_user.get("roles", [])
    organization_id = current_user.get("organization_id")
    
    return await dashboard_service.get_dashboard_overview(
        user_id=current_user["id"],
        user_roles=user_roles,
        organization_id=organization_id,
        academic_year=academic_year,
        semester=semester
    )


@router.get(
    "/user/{user_id}",
    response_model=UserDashboard,
    summary="Get user-specific dashboard"
)
async def get_user_dashboard(
    user_id: int,
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard data for specific user (guru perspective)."""
    return await dashboard_service.get_user_dashboard(
        user_id=user_id,
        requestor_id=current_user["id"],
        requestor_roles=current_user.get("roles", []),
        academic_year=academic_year
    )


@router.get(
    "/organization",
    response_model=OrganizationDashboard,
    summary="Get organization dashboard"
)
async def get_organization_dashboard(
    organization_id: Optional[int] = Query(None, description="Organization ID"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get organization-wide dashboard (kepala sekolah perspective)."""
    # Use current user's organization if not specified
    if not organization_id:
        organization_id = current_user.get("organization_id")
    
    return await dashboard_service.get_organization_dashboard(
        organization_id=organization_id,
        requestor_id=current_user["id"],
        requestor_roles=current_user.get("roles", []),
        academic_year=academic_year,
        semester=semester
    )


@router.get(
    "/admin/overview",
    response_model=AdminDashboard,
    summary="Get admin dashboard"
)
async def get_admin_dashboard(
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get system-wide admin dashboard (super admin perspective)."""
    return await dashboard_service.get_admin_dashboard(
        requestor_id=current_user["id"],
        requestor_roles=current_user.get("roles", []),
        academic_year=academic_year,
        semester=semester
    )


@router.get(
    "/quick-stats",
    response_model=dict,
    summary="Get quick statistics"
)
async def get_quick_stats(
    current_user: dict = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get quick statistics for current user."""
    return await dashboard_service.get_quick_stats(
        user_id=current_user["id"],
        user_roles=current_user.get("roles", []),
        organization_id=current_user.get("organization_id")
    )