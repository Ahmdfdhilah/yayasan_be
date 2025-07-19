"""UserRole repository for unified schema system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user_role import UserRole
from src.models.user import User
from src.models.organization import Organization
from src.schemas.user_role import UserRoleCreate, UserRoleUpdate, UserRoleFilterParams


class UserRoleRepository:
    """UserRole repository for unified schema system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== USER ROLE CRUD OPERATIONS =====
    
    async def create(self, role_data: UserRoleCreate) -> UserRole:
        """Create user role."""
        user_role = UserRole(
            user_id=role_data.user_id,
            role_name=role_data.role_name,
            permissions=role_data.permissions,
            organization_id=role_data.organization_id,
            is_active=role_data.is_active,
            expires_at=role_data.expires_at
        )
        
        self.session.add(user_role)
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role
    
    async def get_by_id(self, role_id: int, include_relations: bool = False) -> Optional[UserRole]:
        """Get user role by ID."""
        query = select(UserRole).where(
            and_(UserRole.id == role_id, UserRole.deleted_at.is_(None))
        )
        
        if include_relations:
            query = query.options(
                selectinload(UserRole.user),
                selectinload(UserRole.organization)
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_user_and_role(self, user_id: int, role_name: str, organization_id: Optional[int] = None) -> Optional[UserRole]:
        """Get user role by user ID and role name."""
        conditions = [
            UserRole.user_id == user_id,
            UserRole.role_name == role_name,
            UserRole.deleted_at.is_(None)
        ]
        
        if organization_id is not None:
            conditions.append(UserRole.organization_id == organization_id)
        else:
            conditions.append(UserRole.organization_id.is_(None))
        
        query = select(UserRole).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, role_id: int, role_data: UserRoleUpdate) -> Optional[UserRole]:
        """Update user role information."""
        user_role = await self.get_by_id(role_id)
        if not user_role:
            return None
        
        # Update fields
        update_data = role_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "permissions" and value:
                # Merge permissions instead of replacing
                if user_role.permissions:
                    user_role.permissions.update(value)
                else:
                    user_role.permissions = value
                continue
            setattr(user_role, key, value)
        
        user_role.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role
    
    async def soft_delete(self, role_id: int) -> bool:
        """Soft delete user role."""
        query = (
            update(UserRole)
            .where(UserRole.id == role_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def deactivate_role(self, role_id: int) -> bool:
        """Deactivate user role."""
        query = (
            update(UserRole)
            .where(UserRole.id == role_id)
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def activate_role(self, role_id: int) -> bool:
        """Activate user role."""
        query = (
            update(UserRole)
            .where(UserRole.id == role_id)
            .values(
                is_active=True,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== USER ROLE FILTERING AND LISTING =====
    
    async def get_all_user_roles_filtered(self, filters: UserRoleFilterParams) -> Tuple[List[UserRole], int]:
        """Get user roles with filters and pagination."""
        # Base query
        query = select(UserRole).where(UserRole.deleted_at.is_(None))
        count_query = select(func.count(UserRole.id)).where(UserRole.deleted_at.is_(None))
        
        # Join with User and Organization for search
        if filters.q:
            query = query.join(User, UserRole.user_id == User.id, isouter=True)
            query = query.join(Organization, UserRole.organization_id == Organization.id, isouter=True)
            count_query = count_query.join(User, UserRole.user_id == User.id, isouter=True)
            count_query = count_query.join(Organization, UserRole.organization_id == Organization.id, isouter=True)
            
            search_filter = or_(
                UserRole.role_name.ilike(f"%{filters.q}%"),
                User.email.ilike(f"%{filters.q}%"),
                Organization.name.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply filters
        if filters.user_id:
            query = query.where(UserRole.user_id == filters.user_id)
            count_query = count_query.where(UserRole.user_id == filters.user_id)
        
        if filters.role_name:
            query = query.where(UserRole.role_name == filters.role_name)
            count_query = count_query.where(UserRole.role_name == filters.role_name)
        
        if filters.organization_id:
            query = query.where(UserRole.organization_id == filters.organization_id)
            count_query = count_query.where(UserRole.organization_id == filters.organization_id)
        
        if filters.is_active is not None:
            query = query.where(UserRole.is_active == filters.is_active)
            count_query = count_query.where(UserRole.is_active == filters.is_active)
        
        if filters.has_permissions is not None:
            if filters.has_permissions:
                query = query.where(UserRole.permissions.is_not(None))
                count_query = count_query.where(UserRole.permissions.is_not(None))
            else:
                query = query.where(UserRole.permissions.is_(None))
                count_query = count_query.where(UserRole.permissions.is_(None))
        
        if filters.expires_soon:
            expires_date = datetime.utcnow() + timedelta(days=filters.expires_soon)
            query = query.where(
                and_(
                    UserRole.expires_at.is_not(None),
                    UserRole.expires_at <= expires_date
                )
            )
            count_query = count_query.where(
                and_(
                    UserRole.expires_at.is_not(None),
                    UserRole.expires_at <= expires_date
                )
            )
        
        if filters.start_date:
            query = query.where(UserRole.created_at >= filters.start_date)
            count_query = count_query.where(UserRole.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.where(UserRole.created_at <= filters.end_date)
            count_query = count_query.where(UserRole.created_at <= filters.end_date)
        
        # Apply sorting
        if filters.sort_by == "role_name":
            sort_column = UserRole.role_name
        elif filters.sort_by == "is_active":
            sort_column = UserRole.is_active
        elif filters.sort_by == "expires_at":
            sort_column = UserRole.expires_at
        elif filters.sort_by == "created_at":
            sort_column = UserRole.created_at
        elif filters.sort_by == "updated_at":
            sort_column = UserRole.updated_at
        else:
            sort_column = UserRole.created_at
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)
        
        user_roles = result.scalars().all()
        total_count = count_result.scalar()
        
        return list(user_roles), total_count
    
    # ===== USER ROLE QUERIES =====
    
    async def get_user_roles(self, user_id: int, active_only: bool = True) -> List[UserRole]:
        """Get all roles for a user."""
        conditions = [
            UserRole.user_id == user_id,
            UserRole.deleted_at.is_(None)
        ]
        
        if active_only:
            conditions.append(UserRole.is_active == True)
            conditions.append(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.utcnow()
                )
            )
        
        query = select(UserRole).where(and_(*conditions)).order_by(UserRole.role_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_users_with_role(self, role_name: str, organization_id: Optional[int] = None, active_only: bool = True) -> List[UserRole]:
        """Get all users with a specific role."""
        conditions = [
            UserRole.role_name == role_name,
            UserRole.deleted_at.is_(None)
        ]
        
        if organization_id is not None:
            conditions.append(UserRole.organization_id == organization_id)
        
        if active_only:
            conditions.append(UserRole.is_active == True)
            conditions.append(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.utcnow()
                )
            )
        
        query = (
            select(UserRole)
            .options(selectinload(UserRole.user))
            .where(and_(*conditions))
            .order_by(UserRole.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def user_has_role(self, user_id: int, role_name: str, organization_id: Optional[int] = None) -> bool:
        """Check if user has a specific role."""
        conditions = [
            UserRole.user_id == user_id,
            UserRole.role_name == role_name,
            UserRole.is_active == True,
            UserRole.deleted_at.is_(None),
            or_(
                UserRole.expires_at.is_(None),
                UserRole.expires_at > datetime.utcnow()
            )
        ]
        
        if organization_id is not None:
            conditions.append(UserRole.organization_id == organization_id)
        else:
            conditions.append(UserRole.organization_id.is_(None))
        
        query = select(UserRole).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def user_has_permission(self, user_id: int, permission: str, organization_id: Optional[int] = None) -> bool:
        """Check if user has a specific permission through any of their roles."""
        conditions = [
            UserRole.user_id == user_id,
            UserRole.is_active == True,
            UserRole.deleted_at.is_(None),
            UserRole.permissions.is_not(None),
            or_(
                UserRole.expires_at.is_(None),
                UserRole.expires_at > datetime.utcnow()
            )
        ]
        
        if organization_id is not None:
            conditions.append(UserRole.organization_id == organization_id)
        
        # Use JSON search for permissions
        permission_condition = text(f"JSON_CONTAINS(permissions, '\"{permission}\"', '$')")
        conditions.append(permission_condition)
        
        query = select(UserRole).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_assign_role(self, user_ids: List[int], role_name: str, organization_id: Optional[int] = None, 
                              permissions: Optional[Dict[str, Any]] = None, expires_at: Optional[datetime] = None) -> int:
        """Bulk assign role to multiple users."""
        created_count = 0
        
        for user_id in user_ids:
            # Check if role already exists
            existing = await self.get_by_user_and_role(user_id, role_name, organization_id)
            if not existing:
                user_role = UserRole(
                    user_id=user_id,
                    role_name=role_name,
                    permissions=permissions,
                    organization_id=organization_id,
                    is_active=True,
                    expires_at=expires_at
                )
                self.session.add(user_role)
                created_count += 1
        
        await self.session.commit()
        return created_count
    
    async def bulk_revoke_role(self, user_ids: List[int], role_name: str, organization_id: Optional[int] = None) -> int:
        """Bulk revoke role from multiple users."""
        conditions = [
            UserRole.user_id.in_(user_ids),
            UserRole.role_name == role_name,
            UserRole.deleted_at.is_(None)
        ]
        
        if organization_id is not None:
            conditions.append(UserRole.organization_id == organization_id)
        else:
            conditions.append(UserRole.organization_id.is_(None))
        
        query = (
            update(UserRole)
            .where(and_(*conditions))
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_update_active_status(self, role_ids: List[int], is_active: bool) -> int:
        """Bulk update active status of roles."""
        query = (
            update(UserRole)
            .where(UserRole.id.in_(role_ids))
            .values(
                is_active=is_active,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_extend_expiry(self, role_ids: List[int], new_expires_at: datetime) -> int:
        """Bulk extend expiry date of roles."""
        query = (
            update(UserRole)
            .where(UserRole.id.in_(role_ids))
            .values(
                expires_at=new_expires_at,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== PERMISSION MANAGEMENT =====
    
    async def update_permissions(self, role_id: int, permissions: Dict[str, Any]) -> bool:
        """Update role permissions."""
        user_role = await self.get_by_id(role_id)
        if not user_role:
            return False
        
        if user_role.permissions:
            user_role.permissions.update(permissions)
        else:
            user_role.permissions = permissions
        
        user_role.updated_at = datetime.utcnow()
        await self.session.commit()
        return True
    
    async def add_permission(self, role_id: int, permission: str, value: Any = True) -> bool:
        """Add a single permission to a role."""
        return await self.update_permissions(role_id, {permission: value})
    
    async def remove_permission(self, role_id: int, permission: str) -> bool:
        """Remove a permission from a role."""
        user_role = await self.get_by_id(role_id)
        if not user_role or not user_role.permissions:
            return False
        
        if permission in user_role.permissions:
            del user_role.permissions[permission]
            user_role.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
        
        return False
    
    # ===== EXPIRY MANAGEMENT =====
    
    async def get_expiring_roles(self, days_ahead: int = 30) -> List[UserRole]:
        """Get roles expiring within specified days."""
        expires_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        query = (
            select(UserRole)
            .options(
                selectinload(UserRole.user),
                selectinload(UserRole.organization)
            )
            .where(
                and_(
                    UserRole.expires_at.is_not(None),
                    UserRole.expires_at <= expires_date,
                    UserRole.is_active == True,
                    UserRole.deleted_at.is_(None)
                )
            )
            .order_by(UserRole.expires_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def cleanup_expired_roles(self) -> int:
        """Deactivate expired roles."""
        query = (
            update(UserRole)
            .where(
                and_(
                    UserRole.expires_at.is_not(None),
                    UserRole.expires_at <= datetime.utcnow(),
                    UserRole.is_active == True,
                    UserRole.deleted_at.is_(None)
                )
            )
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== ANALYTICS =====
    
    async def get_role_analytics(self) -> Dict[str, Any]:
        """Get role assignment analytics."""
        # Total roles
        total_query = select(func.count(UserRole.id)).where(UserRole.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_count = total_result.scalar()
        
        # Active roles
        active_query = select(func.count(UserRole.id)).where(
            and_(
                UserRole.is_active == True,
                UserRole.deleted_at.is_(None),
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.utcnow()
                )
            )
        )
        active_result = await self.session.execute(active_query)
        active_count = active_result.scalar()
        
        # Roles by type
        role_stats_query = (
            select(UserRole.role_name, func.count(UserRole.id))
            .where(
                and_(
                    UserRole.is_active == True,
                    UserRole.deleted_at.is_(None)
                )
            )
            .group_by(UserRole.role_name)
        )
        role_result = await self.session.execute(role_stats_query)
        role_stats = dict(role_result.all())
        
        # Expiring soon (30 days)
        expires_date = datetime.utcnow() + timedelta(days=30)
        expiring_query = select(func.count(UserRole.id)).where(
            and_(
                UserRole.expires_at.is_not(None),
                UserRole.expires_at <= expires_date,
                UserRole.is_active == True,
                UserRole.deleted_at.is_(None)
            )
        )
        expiring_result = await self.session.execute(expiring_query)
        expiring_count = expiring_result.scalar()
        
        return {
            "total_roles": total_count,
            "active_roles": active_count,
            "inactive_roles": total_count - active_count,
            "expiring_soon": expiring_count,
            "by_role_type": role_stats
        }