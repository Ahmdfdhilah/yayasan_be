"""User repository for unified schema system."""

from typing import List, Optional, Tuple, Dict, Any, Union
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, PasswordResetToken
from src.models.enums import UserStatus, UserRole as UserRoleEnum
from src.schemas.user import UserCreate, UserUpdate, AdminUserUpdate
from src.schemas.user import UserFilterParams
from src.auth.jwt import get_password_hash


class UserRepository:
    """User repository for unified schema system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== USER CRUD OPERATIONS =====
    
    async def create(self, user_data: UserCreate, organization_id: Optional[int] = None) -> User:
        """Create user with unified schema."""
        # Default password if not provided
        password = user_data.password if user_data.password else "@Kemendag123"
        hashed_password = get_password_hash(password)
        
        # Create user instance
        user = User(
            email=user_data.email,
            password=hashed_password,
            profile=user_data.profile,
            organization_id=organization_id or user_data.organization_id,
            role=getattr(user_data, 'role', UserRoleEnum.GURU),
            status=user_data.status,
            last_login_at=None,
            remember_token=None
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        from sqlalchemy.orm import selectinload
        from src.models.organization import Organization
        query = select(User).options(
            selectinload(User.organization)
        ).where(
            and_(User.id == user_id, User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        from sqlalchemy.orm import selectinload
        query = select(User).options(
            selectinload(User.organization)
        ).where(
            and_(User.email == email.lower(), User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, user_id: int, user_data: Union[UserUpdate, AdminUserUpdate]) -> Optional[User]:
        """Update user information."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update fields based on schema type
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password."""
        hashed_password = get_password_hash(new_password)
        query = (
            update(User)
            .where(User.id == user_id)
            .values(password=hashed_password, updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user password with already hashed password."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(password=hashed_password, updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def soft_delete(self, user_id: int) -> bool:
        """Soft delete user."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def update_last_login(self, user_id: int) -> None:
        """Update user last login time."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )
        await self.session.execute(query)
        await self.session.commit()
    
    # ===== USER SEARCH AND FILTERING =====
    
    async def search(self, filters: UserFilterParams) -> Tuple[List[User], int]:
        """Search users with filters and pagination."""
        from sqlalchemy.orm import selectinload
        from src.models.organization import Organization
        
        # Base query with relationships
        query = select(User).options(
            selectinload(User.organization)
        ).where(User.deleted_at.is_(None))
        
        # Count query for pagination
        count_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        
        # Apply search filter
        if filters.search:
            search_term = f"%{filters.search}%"
            search_filter = or_(
                User.email.ilike(search_term),
                func.json_extract_path_text(User.profile, 'name').ilike(search_term)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply status filter
        if filters.status:
            query = query.where(User.status == filters.status)
            count_query = count_query.where(User.status == filters.status)
        
        if filters.organization_id:
            query = query.where(User.organization_id == filters.organization_id)
            count_query = count_query.where(User.organization_id == filters.organization_id)
        
        if filters.role:
            # Filter by role directly from user table
            query = query.where(User.role == filters.role)
            count_query = count_query.where(User.role == filters.role)
        
        if filters.is_active is not None:
            if filters.is_active:
                query = query.where(User.status == UserStatus.ACTIVE)
                count_query = count_query.where(User.status == UserStatus.ACTIVE)
            else:
                query = query.where(User.status != UserStatus.ACTIVE)
                count_query = count_query.where(User.status != UserStatus.ACTIVE)
        
        if filters.created_after:
            query = query.where(func.date(User.created_at) >= filters.created_after)
            count_query = count_query.where(func.date(User.created_at) >= filters.created_after)
        
        if filters.created_before:
            query = query.where(func.date(User.created_at) <= filters.created_before)
            count_query = count_query.where(func.date(User.created_at) <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "name":
            sort_column = func.json_extract_path_text(User.profile, 'name')
        elif filters.sort_by == "email":
            sort_column = User.email
        else:
            sort_column = getattr(User, filters.sort_by, User.created_at)
        
        if filters.sort_order == "desc":
            sort_column = sort_column.desc()
        
        query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        users_result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)
        
        users = users_result.scalars().all()
        total = count_result.scalar()
        
        return list(users), total
    
    async def get_users_by_role(self, role_name: str) -> List[User]:
        """Get users by role name."""
        query = select(User).where(
            and_(
                User.role == UserRoleEnum(role_name),
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_users_with_role(self, role_name: str) -> int:
        """Count users with specific role."""
        query = select(func.count(User.id)).where(
            and_(
                User.role == UserRoleEnum(role_name),
                User.deleted_at.is_(None),
                User.status == UserStatus.ACTIVE
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def count_users_with_role_enum(self, role: UserRoleEnum) -> int:
        """Count users with specific role (using enum)."""
        query = select(func.count(User.id)).where(
            and_(
                User.role == role,
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        # Total users
        total_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_users = total_result.scalar()
        
        # Active users
        active_query = select(func.count(User.id)).where(
            and_(
                User.deleted_at.is_(None),
                User.status == UserStatus.ACTIVE
            )
        )
        active_result = await self.session.execute(active_query)
        active_users = active_result.scalar()
        
        # Users by role
        role_stats = {}
        for role in UserRoleEnum:
            count = await self.count_users_with_role(role.value)
            role_stats[role.value] = count
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "role_distribution": role_stats
        }
    
    # ===== ROLE MANAGEMENT =====
    
    async def update_user_role(self, user_id: int, role: UserRoleEnum) -> Optional[User]:
        """Update user role."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.role = role
        user.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    # ===== ORGANIZATION-RELATED METHODS =====
    
    async def get_users_by_organization(self, organization_id: int) -> List[User]:
        """Get all users belonging to a specific organization."""
        query = select(User).where(
            and_(
                User.organization_id == organization_id,
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_users_by_organization(self, organization_id: int) -> int:
        """Count users in specific organization."""
        query = select(func.count(User.id)).where(
            and_(
                User.organization_id == organization_id,
                User.deleted_at.is_(None),
                User.status == UserStatus.ACTIVE
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    # ===== ADMIN QUERIES =====
    
    async def get_all_admins(self) -> List[User]:
        """Get all admin users."""
        query = select(User).where(
            and_(
                User.role == UserRoleEnum.ADMIN,
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_teachers_by_organization(self, organization_id: int) -> List[User]:
        """Get all teachers (guru) in specific organization."""
        query = select(User).where(
            and_(
                User.organization_id == organization_id,
                User.role == UserRoleEnum.GURU,
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_principals_by_organization(self, organization_id: int) -> List[User]:
        """Get all principals (kepala_sekolah) in specific organization."""  
        query = select(User).where(
            and_(
                User.organization_id == organization_id,
                User.role == UserRoleEnum.KEPALA_SEKOLAH,
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_teachers_count_by_organization(self, organization_id: int) -> int:
        """Count teachers (guru) in specific organization."""
        query = select(func.count(User.id)).where(
            and_(
                User.organization_id == organization_id,
                User.role == UserRoleEnum.GURU,
                User.deleted_at.is_(None),
                User.status == UserStatus.ACTIVE
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_user_count(self) -> int:
        """Get total count of active users."""
        query = select(func.count(User.id)).where(
            and_(
                User.deleted_at.is_(None),
                User.status == UserStatus.ACTIVE
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    # ===== PASSWORD RESET METHODS =====
    
    async def create_password_reset_token(self, token_data: dict) -> PasswordResetToken:
        """Create password reset token."""
        token = PasswordResetToken(**token_data)
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token
    
    async def get_password_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token by token value."""
        query = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def mark_token_as_used(self, token_id: str) -> None:
        """Mark password reset token as used."""
        query = (
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used=True, used_at=datetime.utcnow())
        )
        await self.session.execute(query)
        await self.session.commit()
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired password reset tokens."""
        query = delete(PasswordResetToken).where(
            or_(
                PasswordResetToken.expires_at < datetime.utcnow(),
                PasswordResetToken.used == True
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount