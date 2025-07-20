"""User service for unified schema system."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.user import UserRepository
from src.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, 
    UserChangePassword, UserSummary
)
from src.schemas.shared import MessageResponse
from src.schemas.user import UserFilterParams
from src.auth.jwt import get_password_hash, verify_password
from src.models.user import User
from src.models.enums import UserStatus


class UserService:
    """User service for unified schema system."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def _get_user_roles(self, user_id: int) -> List[str]:
        """Helper method to get user roles."""
        user_roles_entities = await self.user_repo.get_user_roles(user_id)
        return [role.role_name for role in user_roles_entities if role.is_active]
    
    async def create_user(self, user_data: UserCreate, organization_id: Optional[int] = None) -> UserResponse:
        """Create user with unified schema."""
        # Validate email uniqueness
        if await self.user_repo.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user in database
        user = await self.user_repo.create(user_data, organization_id)
        
        # Convert to response with roles
        user_roles = await self._get_user_roles(user.id)
        return UserResponse.from_user_model(user, user_roles)
    
    async def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user_roles = await self._get_user_roles(user.id)
        return UserResponse.from_user_model(user, user_roles)
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        user_roles = await self._get_user_roles(user.id)
        return UserResponse.from_user_model(user, user_roles)
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user information."""
        # Check if user exists
        existing_user = await self.user_repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate email uniqueness if being updated
        if hasattr(user_data, 'email') and user_data.email and await self.user_repo.email_exists(user_data.email, exclude_user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Update user in database
        updated_user = await self.user_repo.update(user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        return UserResponse.from_user_model(updated_user)
    
    async def change_password(self, user_id: int, password_data: UserChangePassword) -> MessageResponse:
        """Change user password."""
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(password_data.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Check if new password is different
        if verify_password(password_data.new_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Update password
        new_hashed_password = get_password_hash(password_data.new_password)
        success = await self.user_repo.update_password(user_id, new_hashed_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return MessageResponse(message="Password changed successfully")
    
    async def reset_user_password(self, user_id: int) -> MessageResponse:
        """Reset user password to default (admin only)."""
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Reset to default password
        default_password = "@Kemendag123"
        new_hashed_password = get_password_hash(default_password)
        success = await self.user_repo.update_password(user_id, new_hashed_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
        
        return MessageResponse(message=f"Password reset to default for user {user.display_name}")
    
    async def delete_user(self, user_id: int) -> MessageResponse:
        """Soft delete user."""
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has admin role (prevent deleting last admin)
        user_roles = user.get_roles()
        if "admin" in user_roles:
            admin_count = await self.user_repo.count_users_with_role("admin")
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )
        
        # Soft delete
        await self.user_repo.soft_delete(user_id)
        
        return MessageResponse(message=f"User {user.display_name} deleted successfully")
    
    async def get_all_users_with_filters(self, filters: UserFilterParams) -> UserListResponse:
        """Get users with filters and pagination."""
        # Get users from repository
        users, total = await self.user_repo.get_all_users_filtered(filters)
                
        # Convert to responses with roles
        user_responses = []
        for user in users:
            user_roles = await self._get_user_roles(user.id)
            user_responses.append(UserResponse.from_user_model(user, user_roles))
        
        pages = (total + filters.size - 1) // filters.size if total > 0 else 0

        return UserListResponse(
            items=user_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=pages
        )
    
    async def get_users_by_role(self, role_name: str) -> List[UserResponse]:
        """Get users by role name."""
        users = await self.user_repo.get_users_by_role(role_name)
        # Convert to responses with roles
        user_responses = []
        for user in users:
            user_roles = await self._get_user_roles(user.id)
            user_responses.append(UserResponse.from_user_model(user, user_roles))
        return user_responses
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user for login."""
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Verify password
        if not verify_password(password, user.password):
            return None
        
        # Update last login
        await self.user_repo.update_last_login(user.id)
        
        return user
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        return await self.user_repo.get_user_statistics()
    
    async def activate_user(self, user_id: int) -> UserResponse:
        """Activate user."""
        user_data = UserUpdate(status=UserStatus.ACTIVE)
        return await self.update_user(user_id, user_data)
    
    async def deactivate_user(self, user_id: int) -> UserResponse:
        """Deactivate user."""
        # Check if it's the last admin
        user = await self.user_repo.get_by_id(user_id)
        if user:
            user_roles = user.get_roles()
            if "admin" in user_roles:
                admin_count = await self.user_repo.count_users_with_role("admin")
                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot deactivate the last active admin user"
                    )
        
        user_data = UserUpdate(status=UserStatus.INACTIVE)
        return await self.update_user(user_id, user_data)
    
    async def suspend_user(self, user_id: int) -> UserResponse:
        """Suspend user."""
        user_data = UserUpdate(status=UserStatus.SUSPENDED)
        return await self.update_user(user_id, user_data)
    
    async def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> UserResponse:
        """Update user profile data."""
        user_data = UserUpdate(profile=profile_data)
        return await self.update_user(user_id, user_data)
    
    async def get_user_profile_field(self, user_id: int, field_name: str) -> Optional[str]:
        """Get specific field from user profile."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user.get_profile_field(field_name)
    
    async def update_user_profile_field(self, user_id: int, field_name: str, field_value: str) -> UserResponse:
        """Update specific field in user profile."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update the specific field
        user.update_profile_field(field_name, field_value)
        
        # Save changes
        user_data = UserUpdate(profile=user.profile)
        return await self.update_user(user_id, user_data)