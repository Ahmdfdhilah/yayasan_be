"""Organization repository for unified schema system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.organization import Organization
from src.models.user import User
# Remove OrganizationType import as it's no longer used
from src.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationFilterParams


class OrganizationRepository:
    """Organization repository for unified schema system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== ORGANIZATION CRUD OPERATIONS =====
    
    async def create(self, org_data: OrganizationCreate) -> Organization:
        """Create organization."""
        organization = Organization(
            name=org_data.name,
            description=org_data.description,
            head_id=org_data.head_id
        )
        
        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)
        return organization
    
    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        query = select(Organization).where(
            and_(Organization.id == org_id, Organization.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    
    async def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name."""
        query = select(Organization).where(
            and_(Organization.name == name, Organization.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, org_id: int, org_data: OrganizationUpdate) -> Optional[Organization]:
        """Update organization information."""
        organization = await self.get_by_id(org_id)
        if not organization:
            return None
        
        # Update fields
        update_data = org_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(organization, key, value)
        
        organization.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(organization)
        return organization
    
    async def soft_delete(self, org_id: int) -> bool:
        """Soft delete organization."""
        query = (
            update(Organization)
            .where(Organization.id == org_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def name_exists(self, name: str, exclude_org_id: Optional[int] = None) -> bool:
        """Check if organization name already exists."""
        query = select(Organization).where(
            and_(
                Organization.name == name,
                Organization.deleted_at.is_(None)
            )
        )
        
        if exclude_org_id:
            query = query.where(Organization.id != exclude_org_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    
    # ===== ORGANIZATION FILTERING AND LISTING =====
    
    async def get_all_organizations_filtered(self, filters: OrganizationFilterParams) -> Tuple[List[Organization], int]:
        """Get organizations with filters and pagination."""
        # Base query
        query = select(Organization).where(Organization.deleted_at.is_(None))
        count_query = select(func.count(Organization.id)).where(Organization.deleted_at.is_(None))
        
        # Apply filters
        if filters.q:
            search_filter = or_(
                Organization.name.ilike(f"%{filters.q}%"),
                Organization.description.ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.has_head is not None:
            if filters.has_head:
                query = query.where(Organization.head_id.is_not(None))
                count_query = count_query.where(Organization.head_id.is_not(None))
            else:
                query = query.where(Organization.head_id.is_(None))
                count_query = count_query.where(Organization.head_id.is_(None))
        
        if filters.has_users is not None:
            user_count_subquery = (
                select(func.count(User.id))
                .where(
                    and_(
                        User.organization_id == Organization.id,
                        User.deleted_at.is_(None)
                    )
                )
                .scalar_subquery()
            )
            
            if filters.has_users:
                query = query.where(user_count_subquery > 0)
                count_query = count_query.where(user_count_subquery > 0)
            else:
                query = query.where(user_count_subquery == 0)
                count_query = count_query.where(user_count_subquery == 0)
        
        if filters.start_date:
            query = query.where(Organization.created_at >= filters.start_date)
            count_query = count_query.where(Organization.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.where(Organization.created_at <= filters.end_date)
            count_query = count_query.where(Organization.created_at <= filters.end_date)
        
        # Apply sorting
        if filters.sort_by == "name":
            sort_column = Organization.name
        elif filters.sort_by == "created_at":
            sort_column = Organization.created_at
        elif filters.sort_by == "updated_at":
            sort_column = Organization.updated_at
        else:
            sort_column = Organization.name
        
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
        
        organizations = result.scalars().all()
        total_count = count_result.scalar()
        
        return list(organizations), total_count
    
    async def get_user_count(self, org_id: int) -> int:
        """Get count of users in organization."""
        query = select(func.count(User.id)).where(
            and_(
                User.organization_id == org_id,
                User.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_organizations_with_user_counts(self, org_ids: List[int]) -> Dict[int, int]:
        """Get user counts for multiple organizations."""
        query = (
            select(User.organization_id, func.count(User.id))
            .where(
                and_(
                    User.organization_id.in_(org_ids),
                    User.deleted_at.is_(None)
                )
            )
            .group_by(User.organization_id)
        )
        result = await self.session.execute(query)
        return dict(result.all())
    
    # ===== SPECIALIZED QUERIES =====
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID for validation purposes."""
        query = select(User).where(
            and_(User.id == user_id, User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def search_organizations(self, search_term: str, limit: int = 10) -> List[Organization]:
        """Search organizations by name or description."""
        search_filter = or_(
            Organization.name.ilike(f"%{search_term}%"),
            Organization.description.ilike(f"%{search_term}%")
        )
        
        query = (
            select(Organization)
            .where(
                and_(
                    search_filter,
                    Organization.deleted_at.is_(None)
                )
            )
            .order_by(Organization.name)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_organizations(self, limit: int = 10) -> List[Organization]:
        """Get recently created organizations."""
        query = (
            select(Organization)
            .where(Organization.deleted_at.is_(None))
            .order_by(Organization.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_soft_delete(self, org_ids: List[int]) -> int:
        """Bulk soft delete organizations."""
        query = (
            update(Organization)
            .where(Organization.id.in_(org_ids))
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== ANALYTICS =====
    
    async def get_organization_stats(self) -> Dict[str, Any]:
        """Get organization statistics."""
        # Total count
        total_query = select(func.count(Organization.id)).where(Organization.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_count = total_result.scalar()
        
        # Organizations with users
        with_users_query = (
            select(func.count(func.distinct(User.organization_id)))
            .where(
                and_(
                    User.organization_id.is_not(None),
                    User.deleted_at.is_(None)
                )
            )
        )
        with_users_result = await self.session.execute(with_users_query)
        with_users_count = with_users_result.scalar()
        
        # Organizations with heads
        with_heads_query = (
            select(func.count(Organization.id))
            .where(
                and_(
                    Organization.head_id.is_not(None),
                    Organization.deleted_at.is_(None)
                )
            )
        )
        with_heads_result = await self.session.execute(with_heads_query)
        with_heads_count = with_heads_result.scalar()
        
        return {
            "total_organizations": total_count,
            "organizations_with_users": with_users_count,
            "organizations_without_users": total_count - with_users_count,
            "organizations_with_heads": with_heads_count,
            "organizations_without_heads": total_count - with_heads_count
        }
    
    async def get_organization_count(self) -> int:
        """Get total count of active organizations."""
        query = select(func.count(Organization.id)).where(Organization.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_all(self) -> List[Organization]:
        """Get all active organizations."""
        query = select(Organization).where(Organization.deleted_at.is_(None)).order_by(Organization.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())