"""Organization repository for unified schema system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.organization import Organization
from src.models.user import User
from src.models.enums import OrganizationType
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
            slug=org_data.slug,
            type=org_data.type,
            description=org_data.description,
            image_url=org_data.image_url,
            website_url=org_data.website_url,
            contact_info=org_data.contact_info,
            settings=org_data.settings
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
    
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        query = select(Organization).where(
            and_(Organization.slug == slug, Organization.deleted_at.is_(None))
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
            if key == "contact_info" and value:
                # Merge contact info instead of replacing
                if organization.contact_info:
                    organization.contact_info.update(value)
                else:
                    organization.contact_info = value
                continue
            elif key == "settings" and value:
                # Merge settings instead of replacing
                if organization.settings:
                    organization.settings.update(value)
                else:
                    organization.settings = value
                continue
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
    
    async def slug_exists(self, slug: str, exclude_org_id: Optional[int] = None) -> bool:
        """Check if organization slug already exists."""
        query = select(Organization).where(
            and_(
                Organization.slug == slug,
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
                Organization.description.ilike(f"%{filters.q}%"),
                func.json_unquote(func.json_extract(Organization.contact_info, "$.email")).ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.type:
            query = query.where(Organization.type == filters.type)
            count_query = count_query.where(Organization.type == filters.type)
        
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
        elif filters.sort_by == "type":
            sort_column = Organization.type
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
    
    async def get_by_type(self, org_type: OrganizationType) -> List[Organization]:
        """Get all organizations of a specific type."""
        query = select(Organization).where(
            and_(
                Organization.type == org_type,
                Organization.deleted_at.is_(None)
            )
        ).order_by(Organization.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
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
    
    # ===== CONTACT INFO & SETTINGS MANAGEMENT =====
    
    async def update_contact_info(self, org_id: int, contact_data: Dict[str, Any]) -> bool:
        """Update organization contact information."""
        organization = await self.get_by_id(org_id)
        if not organization:
            return False
        
        if organization.contact_info:
            organization.contact_info.update(contact_data)
        else:
            organization.contact_info = contact_data
        
        organization.updated_at = datetime.utcnow()
        await self.session.commit()
        return True
    
    async def update_settings(self, org_id: int, settings_data: Dict[str, Any]) -> bool:
        """Update organization settings."""
        organization = await self.get_by_id(org_id)
        if not organization:
            return False
        
        if organization.settings:
            organization.settings.update(settings_data)
        else:
            organization.settings = settings_data
        
        organization.updated_at = datetime.utcnow()
        await self.session.commit()
        return True
    
    async def get_contact_info(self, org_id: int, key: str) -> Optional[str]:
        """Get specific contact information."""
        organization = await self.get_by_id(org_id)
        if organization:
            return organization.get_contact_info(key)
        return None
    
    async def get_setting(self, org_id: int, key: str) -> Optional[str]:
        """Get specific organization setting."""
        organization = await self.get_by_id(org_id)
        if organization:
            return organization.get_setting(key)
        return None
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_type(self, org_ids: List[int], new_type: OrganizationType) -> int:
        """Bulk update organization type."""
        query = (
            update(Organization)
            .where(Organization.id.in_(org_ids))
            .values(
                type=new_type,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
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
        # Total organizations by type
        type_stats_query = (
            select(Organization.type, func.count(Organization.id))
            .where(Organization.deleted_at.is_(None))
            .group_by(Organization.type)
        )
        type_result = await self.session.execute(type_stats_query)
        type_stats = dict(type_result.all())
        
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
        
        return {
            "total_organizations": total_count,
            "organizations_with_users": with_users_count,
            "organizations_without_users": total_count - with_users_count,
            "by_type": type_stats
        }