"""Organization management endpoints for unified schema system."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.services.organization import OrganizationService
from src.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, 
    OrganizationListResponse, OrganizationSummary, OrganizationFilterParams,
    AssignHeadRequest, RemoveHeadRequest
)
from src.schemas.shared import MessageResponse
# Remove OrganizationType import as it's no longer used
from src.auth.permissions import get_current_active_user, admin_required, management_roles_required
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_organization_multipart,
    get_organization_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()

# Permission dependencies imported from permissions.py
# admin_required and management_roles_required imported above


async def get_organization_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    """Get organization service dependency."""
    org_repo = OrganizationRepository(session)
    user_repo = UserRepository(session)
    return OrganizationService(org_repo)


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, summary="Create organization")
async def create_organization(
    form_data: Tuple[Dict[str, Any], Optional[UploadFile]] = Depends(get_organization_multipart()),
    current_user: dict = Depends(admin_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Create a new organization with multipart form data.
    
    **Requires admin privileges.**
    
    **Form Data:**
    - data: JSON string containing organization data
    - image: Organization logo/image file (optional)
    
    **JSON Data Fields:**
    - name: Organization name (must be unique)
    - description: Optional description
    - head_id: Optional ID of user to assign as organization head
    """
    json_data, image = form_data
    
    # Handle image upload if provided
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "organizations", uploader)
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create organization data object
    org_data = OrganizationCreate(**complete_data)
    
    return await org_service.create_organization(org_data)


@router.get("/", response_model=OrganizationListResponse, summary="List organizations")
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search query"),
    has_users: Optional[bool] = Query(None, description="Filter organizations with/without users"),
    has_head: Optional[bool] = Query(None, description="Filter organizations with/without head"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get paginated list of organizations with filtering.
    
    Public endpoint - no authentication required.
    
    **Available filters:**
    - Search by name or description
    - Filter by whether organization has users
    - Filter by whether organization has head
    - Sort by various fields
    """
    filters = OrganizationFilterParams(
        page=page,
        size=size,
        q=q,
        has_users=has_users,
        has_head=has_head,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await org_service.get_organizations(filters)




@router.get("/search", response_model=List[OrganizationSummary], summary="Search organizations")
async def search_organizations(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Search organizations by name or description.
    
    Public endpoint - no authentication required.
    """
    return await org_service.search_organizations(q, limit)


@router.get("/recent", response_model=List[OrganizationSummary], summary="Get recent organizations")
async def get_recent_organizations(
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(management_roles_required),
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
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get organization details by ID.
    
    Public endpoint - no authentication required.
    
    Returns detailed organization information including user count.
    """
    return await org_service.get_organization(org_id)




@router.put("/{org_id}", response_model=OrganizationResponse, summary="Update organization")
async def update_organization(
    org_id: int,
    form_data: Tuple[Dict[str, Any], Optional[UploadFile]] = Depends(get_organization_multipart_update()),
    current_user: dict = Depends(management_roles_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update organization information with multipart form data.
    
    **Requires admin or manager privileges.**
    
    **Form Data:**
    - data: JSON string containing organization update data
    - image: Organization logo/image file (optional)
    
    Can update name, description, head assignment, and image.
    """
    json_data, image = form_data
    
    # Handle image upload if provided
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "organizations", uploader)
    
    # Merge image URL with JSON data
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Create organization update data object
    org_data = OrganizationUpdate(**complete_data)
    
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


# ===== HEAD MANAGEMENT =====

@router.post("/{org_id}/assign-head", response_model=OrganizationResponse, summary="Assign head to organization")
async def assign_head(
    org_id: int,
    assign_data: AssignHeadRequest,
    current_user: dict = Depends(management_roles_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Assign a head (kepala sekolah) to an organization.
    
    **Requires admin or manager privileges.**
    
    The user must:
    - Belong to the organization
    - Have 'kepala_sekolah' role
    """
    return await org_service.assign_head(org_id, assign_data)


@router.post("/{org_id}/remove-head", response_model=OrganizationResponse, summary="Remove head from organization")
async def remove_head(
    org_id: int,
    remove_data: RemoveHeadRequest,
    current_user: dict = Depends(management_roles_required),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Remove the current head from an organization.
    
    **Requires admin or manager privileges.**
    
    Requires confirmation to proceed.
    """
    return await org_service.remove_head(org_id, remove_data)


# ===== BULK OPERATIONS =====



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