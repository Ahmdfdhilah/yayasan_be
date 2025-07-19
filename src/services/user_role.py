"""UserRole service for unified schema system."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from src.repositories.user_role import UserRoleRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.schemas.user_role import (
    UserRoleCreate, UserRoleUpdate, UserRoleResponse, UserRoleListResponse,
    UserRoleSummary, UserRoleBulkAssign, UserRoleBulkUpdate, UserRoleBulkDelete,
    PermissionUpdate, RoleAnalytics, RoleAnalyticsResponse
)
from src.schemas.shared import MessageResponse
from src.schemas.filters import UserRoleFilterParams
from src.models.user_role import UserRole


class UserRoleService:
    """UserRole service for unified schema system."""
    
    def __init__(self, role_repo: UserRoleRepository, user_repo: UserRepository, org_repo: OrganizationRepository):
        self.role_repo = role_repo
        self.user_repo = user_repo
        self.org_repo = org_repo
    
    async def create_user_role(self, role_data: UserRoleCreate) -> UserRoleResponse:
        """Create user role."""
        # Validate user exists
        user = await self.user_repo.get_by_id(role_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate organization exists if provided
        if role_data.organization_id:
            organization = await self.org_repo.get_by_id(role_data.organization_id)
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
        
        # Check if role already exists
        existing_role = await self.role_repo.get_by_user_and_role(
            role_data.user_id, 
            role_data.role_name, 
            role_data.organization_id
        )
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has this role in the specified organization"
            )
        
        # Create role in database
        user_role = await self.role_repo.create(role_data)
        
        # Convert to response
        return UserRoleResponse.from_user_role_model(user_role, include_relations=True)
    
    async def get_user_role(self, role_id: int) -> UserRoleResponse:
        """Get user role by ID."""
        user_role = await self.role_repo.get_by_id(role_id, include_relations=True)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        return UserRoleResponse.from_user_role_model(user_role, include_relations=True)
    
    async def update_user_role(self, role_id: int, role_data: UserRoleUpdate) -> UserRoleResponse:
        """Update user role information."""
        # Check if role exists
        existing_role = await self.role_repo.get_by_id(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        # Update role in database
        updated_role = await self.role_repo.update(role_id, role_data)
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user role"
            )
        
        return UserRoleResponse.from_user_role_model(updated_role, include_relations=True)
    
    async def delete_user_role(self, role_id: int) -> MessageResponse:
        """Delete user role (soft delete)."""
        # Check if role exists
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        # Soft delete role
        success = await self.role_repo.soft_delete(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user role"
            )
        
        return MessageResponse(message="User role deleted successfully")
    
    async def get_user_roles(self, filters: UserRoleFilterParams) -> UserRoleListResponse:
        """Get user roles with filters and pagination."""
        user_roles, total_count = await self.role_repo.get_all_user_roles_filtered(filters)
        
        # Convert to response objects
        role_responses = [
            UserRoleResponse.from_user_role_model(role, include_relations=True) 
            for role in user_roles
        ]
        
        # Calculate pagination metadata
        total_pages = (total_count + filters.size - 1) // filters.size
        
        return UserRoleListResponse(
            items=role_responses,
            total=total_count,
            page=filters.page,
            size=filters.size,
            pages=total_pages
        )
    
    async def get_roles_by_user(self, user_id: int, active_only: bool = True) -> List[UserRoleResponse]:
        """Get all roles for a specific user."""
        # Validate user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_roles = await self.role_repo.get_user_roles(user_id, active_only)
        
        return [
            UserRoleResponse.from_user_role_model(role, include_relations=True) 
            for role in user_roles
        ]
    
    async def get_users_with_role(self, role_name: str, organization_id: Optional[int] = None, active_only: bool = True) -> List[UserRoleResponse]:
        """Get all users with a specific role."""
        # Validate organization exists if provided
        if organization_id:
            organization = await self.org_repo.get_by_id(organization_id)
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
        
        user_roles = await self.role_repo.get_users_with_role(role_name, organization_id, active_only)
        
        return [
            UserRoleResponse.from_user_role_model(role, include_relations=True) 
            for role in user_roles
        ]
    
    async def user_has_role(self, user_id: int, role_name: str, organization_id: Optional[int] = None) -> bool:
        """Check if user has a specific role."""
        return await self.role_repo.user_has_role(user_id, role_name, organization_id)
    
    async def user_has_permission(self, user_id: int, permission: str, organization_id: Optional[int] = None) -> bool:
        """Check if user has a specific permission."""
        return await self.role_repo.user_has_permission(user_id, permission, organization_id)
    
    # ===== ROLE ASSIGNMENT AND MANAGEMENT =====
    
    async def assign_role(self, user_id: int, role_name: str, organization_id: Optional[int] = None, 
                         permissions: Optional[Dict[str, Any]] = None, expires_at: Optional[datetime] = None) -> UserRoleResponse:
        """Assign role to user."""
        role_data = UserRoleCreate(
            user_id=user_id,
            role_name=role_name,
            permissions=permissions,
            organization_id=organization_id,
            expires_at=expires_at
        )
        
        return await self.create_user_role(role_data)
    
    async def revoke_role(self, user_id: int, role_name: str, organization_id: Optional[int] = None) -> MessageResponse:
        """Revoke role from user."""
        # Find the role
        user_role = await self.role_repo.get_by_user_and_role(user_id, role_name, organization_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        # Delete the role
        return await self.delete_user_role(user_role.id)
    
    async def activate_role(self, role_id: int) -> MessageResponse:
        """Activate user role."""
        # Check if role exists
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        success = await self.role_repo.activate_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate user role"
            )
        
        return MessageResponse(message="User role activated successfully")
    
    async def deactivate_role(self, role_id: int) -> MessageResponse:
        """Deactivate user role."""
        # Check if role exists
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        success = await self.role_repo.deactivate_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user role"
            )
        
        return MessageResponse(message="User role deactivated successfully")
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_assign_role(self, bulk_data: UserRoleBulkAssign) -> MessageResponse:
        """Bulk assign role to multiple users."""
        # Validate all users exist
        for user_id in bulk_data.user_ids:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found"
                )
        
        # Validate organization exists if provided
        if bulk_data.organization_id:
            organization = await self.org_repo.get_by_id(bulk_data.organization_id)
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
        
        # Perform bulk assignment
        created_count = await self.role_repo.bulk_assign_role(
            bulk_data.user_ids,
            bulk_data.role_name,
            bulk_data.organization_id,
            bulk_data.permissions,
            bulk_data.expires_at
        )
        
        return MessageResponse(
            message=f"Successfully assigned role '{bulk_data.role_name}' to {created_count} users"
        )
    
    async def bulk_revoke_role(self, user_ids: List[int], role_name: str, organization_id: Optional[int] = None) -> MessageResponse:
        """Bulk revoke role from multiple users."""
        # Validate all users exist
        for user_id in user_ids:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found"
                )
        
        # Perform bulk revocation
        revoked_count = await self.role_repo.bulk_revoke_role(user_ids, role_name, organization_id)
        
        return MessageResponse(
            message=f"Successfully revoked role '{role_name}' from {revoked_count} users"
        )
    
    async def bulk_update_roles(self, bulk_data: UserRoleBulkUpdate) -> MessageResponse:
        """Bulk update user roles."""
        # Validate all roles exist
        for role_id in bulk_data.role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User role {role_id} not found"
                )
        
        # Perform bulk update
        if bulk_data.is_active is not None:
            updated_count = await self.role_repo.bulk_update_active_status(bulk_data.role_ids, bulk_data.is_active)
        
        if bulk_data.expires_at is not None:
            updated_count = await self.role_repo.bulk_extend_expiry(bulk_data.role_ids, bulk_data.expires_at)
        
        return MessageResponse(
            message=f"Successfully updated {updated_count} user roles"
        )
    
    async def bulk_delete_roles(self, bulk_data: UserRoleBulkDelete) -> MessageResponse:
        """Bulk delete user roles."""
        # Validate all roles exist unless force delete
        if not bulk_data.force_delete:
            for role_id in bulk_data.role_ids:
                role = await self.role_repo.get_by_id(role_id)
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User role {role_id} not found"
                    )
        
        # Perform bulk delete (soft delete)
        deleted_count = 0
        for role_id in bulk_data.role_ids:
            success = await self.role_repo.soft_delete(role_id)
            if success:
                deleted_count += 1
        
        return MessageResponse(
            message=f"Successfully deleted {deleted_count} user roles"
        )
    
    # ===== PERMISSION MANAGEMENT =====
    
    async def update_permissions(self, role_id: int, permission_data: PermissionUpdate) -> UserRoleResponse:
        """Update role permissions."""
        # Check if role exists
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        # Update permissions
        success = await self.role_repo.update_permissions(role_id, permission_data.permissions)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update permissions"
            )
        
        # Return updated role
        return await self.get_user_role(role_id)
    
    async def add_permission(self, role_id: int, permission: str, value: Any = True) -> UserRoleResponse:
        """Add a single permission to a role."""
        # Check if role exists
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        # Add permission
        success = await self.role_repo.add_permission(role_id, permission, value)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add permission"
            )
        
        # Return updated role
        return await self.get_user_role(role_id)
    
    async def remove_permission(self, role_id: int, permission: str) -> UserRoleResponse:
        """Remove a permission from a role."""
        # Check if role exists
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        
        # Remove permission
        success = await self.role_repo.remove_permission(role_id, permission)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission not found in role"
            )
        
        # Return updated role
        return await self.get_user_role(role_id)
    
    # ===== EXPIRY MANAGEMENT =====
    
    async def get_expiring_roles(self, days_ahead: int = 30) -> List[UserRoleResponse]:
        """Get roles expiring within specified days."""
        user_roles = await self.role_repo.get_expiring_roles(days_ahead)
        
        return [
            UserRoleResponse.from_user_role_model(role, include_relations=True) 
            for role in user_roles
        ]
    
    async def cleanup_expired_roles(self) -> MessageResponse:
        """Deactivate expired roles."""
        deactivated_count = await self.role_repo.cleanup_expired_roles()
        
        return MessageResponse(
            message=f"Successfully deactivated {deactivated_count} expired roles"
        )
    
    # ===== ANALYTICS =====
    
    async def get_role_analytics(self) -> RoleAnalyticsResponse:
        """Get role assignment analytics."""
        analytics = await self.role_repo.get_role_analytics()
        
        # Convert to response format
        summary = {
            "total_roles": len(analytics.get("by_role_type", {})),
            "total_assignments": sum(analytics.get("by_role_type", {}).values())
        }
        by_role = []
        
        for role_name, count in analytics["by_role_type"].items():
            by_role.append(RoleAnalytics(
                role_name=role_name,
                total_users=count,
                active_users=count,  # This would need more detailed query
                inactive_users=0,
                users_by_organization={},
                expiring_soon_count=0
            ))
        
        return RoleAnalyticsResponse(
            summary=summary,
            by_role=by_role,
            by_organization={},
            recent_assignments=0,  # Would need additional queries
            recent_revocations=0
        )
    
    # ===== VALIDATION HELPERS =====
    
    async def validate_user_role_exists(self, role_id: int) -> UserRole:
        """Validate user role exists and return it."""
        user_role = await self.role_repo.get_by_id(role_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found"
            )
        return user_role