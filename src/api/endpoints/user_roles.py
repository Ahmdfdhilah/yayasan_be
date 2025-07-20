"""User Role management endpoints for unified schema system."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.user_role import UserRoleRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.services.user_role import UserRoleService
from src.schemas.user_role import (
    UserRoleCreate, UserRoleUpdate, UserRoleResponse, UserRoleListResponse,
    UserRoleSummary, UserRoleFilterParams, UserRoleBulkAssign, UserRoleBulkUpdate,
    UserRoleBulkDelete, PermissionUpdate, RoleAnalyticsResponse
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user, require_roles

router = APIRouter()

# Permission dependencies
admin_required = require_roles(["admin"])
admin_or_manager = require_roles(["admin", "kepala_sekolah"])


async def get_user_role_service(session: AsyncSession = Depends(get_db)) -> UserRoleService:
    """Get user role service dependency."""
    role_repo = UserRoleRepository(session)
    user_repo = UserRepository(session)
    org_repo = OrganizationRepository(session)
    return UserRoleService(role_repo, user_repo, org_repo)


@router.post("/", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED, summary="Create user role")
async def create_user_role(
    role_data: UserRoleCreate,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Create a new user role assignment.
    
    **Requires admin privileges.**
    
    - **user_id**: User to assign role to
    - **role_name**: Name of the role
    - **permissions**: Optional permissions object
    - **organization_id**: Optional organization context
    - **expires_at**: Optional expiration date
    """
    return await role_service.create_user_role(role_data)


@router.get("/", response_model=UserRoleListResponse, summary="List user roles")
async def list_user_roles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search query"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    role_name: Optional[str] = Query(None, description="Filter by role name"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    expires_soon: Optional[int] = Query(None, ge=1, le=365, description="Expiring within N days"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(admin_or_manager),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Get paginated list of user roles with filtering.
    
    **Requires admin or manager privileges.**
    
    **Available filters:**
    - Search by role name, user email, or organization name
    - Filter by user, role, or organization
    - Filter by active status
    - Filter by expiration date
    """
    filters = UserRoleFilterParams(
        page=page,
        size=size,
        q=q,
        user_id=user_id,
        role_name=role_name,
        organization_id=organization_id,
        is_active=is_active,
        expires_soon=expires_soon,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await role_service.get_user_roles(filters)


@router.get("/analytics", response_model=RoleAnalyticsResponse, summary="Get role analytics")
async def get_role_analytics(
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Get role assignment analytics and statistics.
    
    **Requires admin privileges.**
    """
    return await role_service.get_role_analytics()


@router.get("/expiring", response_model=List[UserRoleResponse], summary="Get expiring roles")
async def get_expiring_roles(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to check"),
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Get roles expiring within specified days.
    
    **Requires admin privileges.**
    """
    return await role_service.get_expiring_roles(days_ahead)


@router.post("/cleanup-expired", response_model=MessageResponse, summary="Cleanup expired roles")
async def cleanup_expired_roles(
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Deactivate all expired roles.
    
    **Requires admin privileges.**
    """
    return await role_service.cleanup_expired_roles()


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse], summary="Get user's roles")
async def get_user_roles(
    user_id: int,
    active_only: bool = Query(True, description="Only return active roles"),
    current_user: dict = Depends(admin_or_manager),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Get all roles for a specific user.
    
    **Requires admin or manager privileges.**
    """
    return await role_service.get_roles_by_user(user_id, active_only)


@router.get("/roles/{role_name}/users", response_model=List[UserRoleResponse], summary="Get users with role")
async def get_users_with_role(
    role_name: str,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    active_only: bool = Query(True, description="Only return active assignments"),
    current_user: dict = Depends(admin_or_manager),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Get all users with a specific role.
    
    **Requires admin or manager privileges.**
    """
    return await role_service.get_users_with_role(role_name, organization_id, active_only)


@router.get("/{role_id}", response_model=UserRoleResponse, summary="Get user role by ID")
async def get_user_role(
    role_id: int,
    current_user: dict = Depends(admin_or_manager),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Get user role details by ID.
    
    **Requires admin or manager privileges.**
    """
    return await role_service.get_user_role(role_id)


@router.put("/{role_id}", response_model=UserRoleResponse, summary="Update user role")
async def update_user_role(
    role_id: int,
    role_data: UserRoleUpdate,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Update user role information.
    
    **Requires admin privileges.**
    """
    return await role_service.update_user_role(role_id, role_data)


@router.delete("/{role_id}", response_model=MessageResponse, summary="Delete user role")
async def delete_user_role(
    role_id: int,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Delete user role assignment.
    
    **Requires admin privileges.**
    """
    return await role_service.delete_user_role(role_id)


# ===== ROLE ASSIGNMENT OPERATIONS =====

@router.post("/assign", response_model=UserRoleResponse, summary="Assign role to user")
async def assign_role(
    user_id: int,
    role_name: str,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    expires_at: Optional[datetime] = Query(None, description="Role expiration date"),
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Assign a role to a user.
    
    **Requires admin privileges.**
    """
    return await role_service.assign_role(user_id, role_name, organization_id, None, expires_at)


@router.post("/revoke", response_model=MessageResponse, summary="Revoke role from user")
async def revoke_role(
    user_id: int,
    role_name: str,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Revoke a role from a user.
    
    **Requires admin privileges.**
    """
    return await role_service.revoke_role(user_id, role_name, organization_id)


@router.post("/{role_id}/activate", response_model=MessageResponse, summary="Activate user role")
async def activate_role(
    role_id: int,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Activate a user role.
    
    **Requires admin privileges.**
    """
    return await role_service.activate_role(role_id)


@router.post("/{role_id}/deactivate", response_model=MessageResponse, summary="Deactivate user role")
async def deactivate_role(
    role_id: int,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Deactivate a user role.
    
    **Requires admin privileges.**
    """
    return await role_service.deactivate_role(role_id)


# ===== PERMISSION MANAGEMENT =====

@router.put("/{role_id}/permissions", response_model=UserRoleResponse, summary="Update role permissions")
async def update_permissions(
    role_id: int,
    permission_data: PermissionUpdate,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Update role permissions.
    
    **Requires admin privileges.**
    """
    return await role_service.update_permissions(role_id, permission_data)


@router.post("/{role_id}/permissions/{permission}", response_model=UserRoleResponse, summary="Add permission")
async def add_permission(
    role_id: int,
    permission: str,
    value: bool = Query(True, description="Permission value"),
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Add a single permission to a role.
    
    **Requires admin privileges.**
    """
    return await role_service.add_permission(role_id, permission, value)


@router.delete("/{role_id}/permissions/{permission}", response_model=UserRoleResponse, summary="Remove permission")
async def remove_permission(
    role_id: int,
    permission: str,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Remove a permission from a role.
    
    **Requires admin privileges.**
    """
    return await role_service.remove_permission(role_id, permission)


# ===== BULK OPERATIONS =====

@router.post("/bulk/assign", response_model=MessageResponse, summary="Bulk assign role")
async def bulk_assign_role(
    bulk_data: UserRoleBulkAssign,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Assign role to multiple users.
    
    **Requires admin privileges.**
    """
    return await role_service.bulk_assign_role(bulk_data)


@router.post("/bulk/revoke", response_model=MessageResponse, summary="Bulk revoke role")
async def bulk_revoke_role(
    user_ids: List[int],
    role_name: str,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Revoke role from multiple users.
    
    **Requires admin privileges.**
    """
    return await role_service.bulk_revoke_role(user_ids, role_name, organization_id)


@router.put("/bulk/update", response_model=MessageResponse, summary="Bulk update roles")
async def bulk_update_roles(
    bulk_data: UserRoleBulkUpdate,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Bulk update user roles.
    
    **Requires admin privileges.**
    """
    return await role_service.bulk_update_roles(bulk_data)


@router.delete("/bulk", response_model=MessageResponse, summary="Bulk delete roles")
async def bulk_delete_roles(
    bulk_data: UserRoleBulkDelete,
    current_user: dict = Depends(admin_required),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Bulk delete user roles.
    
    **Requires admin privileges.**
    """
    return await role_service.bulk_delete_roles(bulk_data)


# ===== VALIDATION ENDPOINTS =====

@router.get("/check/{user_id}/role/{role_name}", response_model=bool, summary="Check if user has role")
async def check_user_has_role(
    user_id: int,
    role_name: str,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    current_user: dict = Depends(admin_or_manager),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Check if user has a specific role.
    
    **Requires admin or manager privileges.**
    """
    return await role_service.user_has_role(user_id, role_name, organization_id)


@router.get("/check/{user_id}/permission/{permission}", response_model=bool, summary="Check if user has permission")
async def check_user_has_permission(
    user_id: int,
    permission: str,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    current_user: dict = Depends(admin_or_manager),
    role_service: UserRoleService = Depends(get_user_role_service)
):
    """
    Check if user has a specific permission.
    
    **Requires admin or manager privileges.**
    """
    return await role_service.user_has_permission(user_id, permission, organization_id)