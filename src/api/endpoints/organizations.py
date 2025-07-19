"""Organization management endpoints for unified schema system."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.services.organization import OrganizationService
from src.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, 
    OrganizationListResponse, OrganizationSummary, OrganizationFilterParams,
    ContactInfoUpdate, SettingsUpdate
)
from src.schemas.shared import MessageResponse
from src.models.enums import OrganizationType
from src.auth.permissions import get_current_active_user, require_roles

router = APIRouter()

# Permission dependencies
admin_required = require_roles(["admin", "super_admin"])
admin_or_manager = require_roles(["admin", "super_admin", "kepala_sekolah"])


async def get_organization_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    """Get organization service dependency."""
    org_repo = OrganizationRepository(session)
    user_repo = UserRepository(session)
    return OrganizationService(org_repo)


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, summary="Create organization")
async def create_organization(
    org_data: OrganizationCreate,
    current_user: dict = Depends(admin_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Create a new organization.
    
    **Requires admin privileges.**
    
    - **name**: Organization name (must be unique)
    - **slug**: URL-friendly identifier (optional, must be unique)
    - **type**: Organization type (school, foundation, department)
    - **description**: Optional description
    - **contact_info**: Contact information as JSON
    - **settings**: Organization-specific settings as JSON
    """
    return await org_service.create_organization(org_data)


@router.get("/", response_model=OrganizationListResponse, summary="List organizations")
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search query"),
    type: Optional[OrganizationType] = Query(None, description="Filter by organization type"),
    has_users: Optional[bool] = Query(None, description="Filter organizations with/without users"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get paginated list of organizations with filtering.
    
    **Available filters:**
    - Search by name, description, or contact info
    - Filter by organization type
    - Filter by whether organization has users
    - Sort by various fields
    """
    filters = OrganizationFilterParams(
        page=page,
        size=size,
        q=q,
        type=type,
        has_users=has_users,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await org_service.get_organizations(filters)


@router.get("/types/{org_type}", response_model=List[OrganizationSummary], summary="Get organizations by type")
async def get_organizations_by_type(
    org_type: OrganizationType,
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get all organizations of a specific type.
    """
    return await org_service.get_organizations_by_type(org_type)


@router.get("/search", response_model=List[OrganizationSummary], summary="Search organizations")
async def search_organizations(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Search organizations by name or description.
    """
    return await org_service.search_organizations(q, limit)


@router.get("/recent", response_model=List[OrganizationSummary], summary="Get recent organizations")
async def get_recent_organizations(
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(admin_or_manager),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get recently created organizations.
    
    **Requires admin or manager privileges.**
    """
    return await org_service.get_recent_organizations(limit)


@router.get("/analytics", response_model=Dict[str, Any], summary="Get organization analytics")
async def get_organization_analytics(
    current_user: dict = Depends(admin_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get organization statistics and analytics.
    
    **Requires admin privileges.**
    
    Returns counts by type, utilization rates, etc.
    """
    return await org_service.get_organization_analytics()


@router.get("/{org_id}", response_model=OrganizationResponse, summary="Get organization by ID")
async def get_organization(
    org_id: int,
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get organization details by ID.
    
    Returns detailed organization information including user count.
    """
    return await org_service.get_organization(org_id)


@router.get("/slug/{slug}", response_model=OrganizationResponse, summary="Get organization by slug")
async def get_organization_by_slug(
    slug: str,
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get organization details by slug.
    """
    return await org_service.get_organization_by_slug(slug)


@router.put("/{org_id}", response_model=OrganizationResponse, summary="Update organization")
async def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    current_user: dict = Depends(admin_or_manager),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update organization information.
    
    **Requires admin or manager privileges.**
    
    Can update basic info, contact information, and settings.
    """
    return await org_service.update_organization(org_id, org_data)


@router.delete("/{org_id}", response_model=MessageResponse, summary="Delete organization")
async def delete_organization(
    org_id: int,
    current_user: dict = Depends(admin_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Delete organization (soft delete).
    
    **Requires admin privileges.**
    
    Cannot delete organizations that have users assigned.
    """
    return await org_service.delete_organization(org_id)


# ===== CONTACT INFO MANAGEMENT =====

@router.put("/{org_id}/contact", response_model=OrganizationResponse, summary="Update contact information")
async def update_contact_info(
    org_id: int,
    contact_data: ContactInfoUpdate,
    current_user: dict = Depends(admin_or_manager),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update organization contact information.
    
    **Requires admin or manager privileges.**
    """
    return await org_service.update_contact_info(org_id, contact_data)


@router.get("/{org_id}/contact/{key}", response_model=str, summary="Get specific contact info")
async def get_contact_info(
    org_id: int,
    key: str,
    current_user: dict = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get specific contact information by key.
    """
    return await org_service.get_contact_info(org_id, key)


# ===== SETTINGS MANAGEMENT =====

@router.put("/{org_id}/settings", response_model=OrganizationResponse, summary="Update organization settings")
async def update_settings(
    org_id: int,
    settings_data: SettingsUpdate,
    current_user: dict = Depends(admin_or_manager),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update organization settings.
    
    **Requires admin or manager privileges.**
    """
    return await org_service.update_settings(org_id, settings_data)


@router.get("/{org_id}/settings/{key}", response_model=str, summary="Get specific setting")
async def get_setting(
    org_id: int,
    key: str,
    current_user: dict = Depends(admin_or_manager),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get specific organization setting by key.
    
    **Requires admin or manager privileges.**
    """
    return await org_service.get_setting(org_id, key)


# ===== BULK OPERATIONS =====

@router.put("/bulk/type", response_model=MessageResponse, summary="Bulk update organization type")
async def bulk_update_type(
    org_ids: List[int],
    new_type: OrganizationType,
    current_user: dict = Depends(admin_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Bulk update organization type for multiple organizations.
    
    **Requires admin privileges.**
    """
    return await org_service.bulk_update_type(org_ids, new_type)


@router.delete("/bulk", response_model=MessageResponse, summary="Bulk delete organizations")
async def bulk_delete_organizations(
    org_ids: List[int],
    force: bool = Query(False, description="Force delete organizations with users"),
    current_user: dict = Depends(admin_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Bulk delete multiple organizations.
    
    **Requires admin privileges.**
    
    Use force=true to delete organizations that have users.
    """
    return await org_service.bulk_delete_organizations(org_ids, force)