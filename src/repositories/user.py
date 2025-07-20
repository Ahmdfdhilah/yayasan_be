"""User repository for unified schema system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, PasswordResetToken
from src.models.user_role import UserRole
from src.models.enums import UserStatus
from src.schemas.user import UserCreate, UserUpdate
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
        query = select(User).options(selectinload(User.user_roles)).where(
            and_(User.id == user_id, User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(
            and_(User.email == email.lower(), User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is None:
                # Skip setting None values to avoid null constraint violations
                continue
            elif key == "email" and value:
                # Normalize email
                value = value.lower()
            elif key == "profile" and value:
                # Replace profile data completely
                user.profile = value
                continue
            setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_password(self, user_id: int, new_hashed_password: str) -> bool:
        """Update user password."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                password=new_hashed_password,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def soft_delete(self, user_id: int) -> bool:
        """Soft delete user."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email already exists."""
        query = select(User).where(
            and_(
                User.email == email.lower(),
                User.deleted_at.is_(None)
            )
        )
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ===== USER FILTERING AND LISTING =====
    
    async def get_all_users_filtered(self, filters: UserFilterParams) -> Tuple[List[User], int]:
        """Get users with filters and pagination."""
        # Base query
        query = select(User).where(User.deleted_at.is_(None))
        count_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        
        # Apply filters
        if filters.search:
            search_filter = or_(
                User.email.ilike(f"%{filters.search}%"),
                func.json_extract_path_text(User.profile, 'name').ilike(f"%{filters.search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.status:
            query = query.where(User.status == filters.status)
            count_query = count_query.where(User.status == filters.status)
        
        if filters.organization_id:
            query = query.where(User.organization_id == filters.organization_id)
            count_query = count_query.where(User.organization_id == filters.organization_id)
        
        if filters.is_active is not None:
            if filters.is_active:
                query = query.where(User.status == UserStatus.ACTIVE)
                count_query = count_query.where(User.status == UserStatus.ACTIVE)
            else:
                query = query.where(User.status != UserStatus.ACTIVE)
                count_query = count_query.where(User.status != UserStatus.ACTIVE)
        
        if filters.created_after:
            query = query.where(User.created_at >= filters.created_after)
            count_query = count_query.where(User.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(User.created_at <= filters.created_before)
            count_query = count_query.where(User.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "email":
            sort_column = User.email
        elif filters.sort_by == "created_at":
            sort_column = User.created_at
        elif filters.sort_by == "updated_at":
            sort_column = User.updated_at
        elif filters.sort_by == "status":
            sort_column = User.status
        else:
            sort_column = User.created_at
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(users), total
    
    async def get_users_by_role(self, role_name: str) -> List[User]:
        """Get users by role name."""
        query = (
            select(User)
            .join(UserRole)
            .where(
                and_(
                    UserRole.role_name == role_name,
                    UserRole.is_active == True,
                    User.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_users_with_role(self, role_name: str) -> int:
        """Count users with specific role."""
        query = (
            select(func.count(User.id))
            .join(UserRole)
            .where(
                and_(
                    UserRole.role_name == role_name,
                    UserRole.is_active == True,
                    User.deleted_at.is_(None),
                    User.status == UserStatus.ACTIVE
                )
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
            and_(User.deleted_at.is_(None), User.status == UserStatus.ACTIVE)
        )
        active_result = await self.session.execute(active_query)
        active_users = active_result.scalar()
        
        # Users by status
        status_query = (
            select(User.status, func.count(User.id))
            .where(User.deleted_at.is_(None))
            .group_by(User.status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = dict(status_result.fetchall())
        
        # Users created in last 30 days
        thirty_days_ago = datetime.utcnow() - datetime.timedelta(days=30)
        recent_query = select(func.count(User.id)).where(
            and_(
                User.deleted_at.is_(None),
                User.created_at >= thirty_days_ago
            )
        )
        recent_result = await self.session.execute(recent_query)
        recent_users = recent_result.scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": status_counts.get(UserStatus.INACTIVE, 0),
            "suspended_users": status_counts.get(UserStatus.SUSPENDED, 0),
            "recent_users": recent_users,
            "status_distribution": status_counts
        }
    
    # ===== PASSWORD RESET TOKEN OPERATIONS =====
    
    async def create_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> PasswordResetToken:
        """Create password reset token."""
        import uuid
        reset_token = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used=False,
            used_at=None
        )
        
        self.session.add(reset_token)
        await self.session.commit()
        await self.session.refresh(reset_token)
        return reset_token
    
    async def get_password_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token by token string."""
        query = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def use_password_reset_token(self, token: str) -> bool:
        """Mark password reset token as used."""
        query = (
            update(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .values(
                used=True,
                used_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== USER ROLE OPERATIONS =====
    
    async def add_user_role(self, user_id: int, role_name: str, permissions: Optional[Dict[str, Any]] = None, 
                           organization_id: Optional[int] = None, expires_at: Optional[datetime] = None) -> UserRole:
        """Add role to user."""
        user_role = UserRole(
            user_id=user_id,
            role_name=role_name,
            permissions=permissions,
            organization_id=organization_id,
            is_active=True,
            expires_at=expires_at
        )
        
        self.session.add(user_role)
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role
    
    async def remove_user_role(self, user_id: int, role_name: str, organization_id: Optional[int] = None) -> bool:
        """Remove role from user."""
        query = (
            update(UserRole)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_name == role_name,
                    UserRole.organization_id == organization_id if organization_id else True
                )
            )
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_user_roles(self, user_id: int) -> List[UserRole]:
        """Get all active roles for user."""
        query = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                UserRole.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
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
    
    async def get_teachers_by_organization(self, organization_id: int) -> List[User]:
        """Get all teachers (guru) in a specific organization."""
        query = (
            select(User)
            .join(UserRole)
            .where(
                and_(
                    User.organization_id == organization_id,
                    UserRole.role_name == "guru",
                    UserRole.is_active == True,
                    User.deleted_at.is_(None),
                    User.status == UserStatus.ACTIVE
                )
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
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
    
    async def get_users_count_by_organization(self, organization_id: int) -> int:
        """Get count of users in a specific organization."""
        query = select(func.count(User.id)).where(
            and_(
                User.organization_id == organization_id,
                User.deleted_at.is_(None),
                User.status == UserStatus.ACTIVE
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_teachers_count_by_organization(self, organization_id: int) -> int:
        """Get count of teachers in a specific organization."""
        query = (
            select(func.count(User.id))
            .join(UserRole)
            .where(
                and_(
                    User.organization_id == organization_id,
                    UserRole.role_name == "guru",
                    UserRole.is_active == True,
                    User.deleted_at.is_(None),
                    User.status == UserStatus.ACTIVE
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0