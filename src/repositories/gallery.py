"""Gallery repository for CRUD and ordering operations."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gallery import Gallery
from src.schemas.gallery import GalleryCreate, GalleryUpdate, GalleryFilterParams


class GalleryRepository:
    """Gallery repository for CRUD and ordering operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, gallery_data: GalleryCreate, created_by: Optional[int] = None) -> Gallery:
        """Create a new gallery item."""
        gallery = Gallery(
            img_url=gallery_data.img_url,
            title=gallery_data.title,
            excerpt=gallery_data.excerpt,
            is_active=gallery_data.is_active,
            display_order=gallery_data.display_order,
            created_by=created_by
        )
        
        self.session.add(gallery)
        await self.session.commit()
        await self.session.refresh(gallery)
        return gallery
    
    async def get_by_id(self, gallery_id: int) -> Optional[Gallery]:
        """Get gallery item by ID."""
        query = select(Gallery).where(
            and_(Gallery.id == gallery_id, Gallery.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, gallery_id: int, gallery_data: GalleryUpdate, updated_by: Optional[int] = None) -> Optional[Gallery]:
        """Update gallery item information."""
        gallery = await self.get_by_id(gallery_id)
        if not gallery:
            return None
        
        # Update fields
        update_data = gallery_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(gallery, key, value)
        
        gallery.updated_at = datetime.utcnow()
        gallery.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(gallery)
        return gallery
    
    async def soft_delete(self, gallery_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete gallery item."""
        query = (
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def hard_delete(self, gallery_id: int) -> bool:
        """Permanently delete gallery item."""
        query = delete(Gallery).where(Gallery.id == gallery_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== FILTERING AND LISTING =====
    
    async def get_all_filtered(self, filters: GalleryFilterParams) -> Tuple[List[Gallery], int]:
        """Get gallery items with filters and pagination."""
        # Base query
        query = select(Gallery).where(Gallery.deleted_at.is_(None))
        count_query = select(func.count(Gallery.id)).where(Gallery.deleted_at.is_(None))
        
        # Apply filters
        if filters.search:
            search_filter = Gallery.title.ilike(f"%{filters.search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.is_active is not None:
            query = query.where(Gallery.is_active == filters.is_active)
            count_query = count_query.where(Gallery.is_active == filters.is_active)
        
        # Apply sorting
        if filters.sort_by == "title":
            sort_column = Gallery.title
        elif filters.sort_by == "created_at":
            sort_column = Gallery.created_at
        elif filters.sort_by == "updated_at":
            sort_column = Gallery.updated_at
        else:
            sort_column = Gallery.display_order
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        galleries = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(galleries), total
    
    async def get_active_galleries(self, limit: Optional[int] = None) -> List[Gallery]:
        """Get active gallery items only."""
        query = select(Gallery).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_active == True
            )
        ).order_by(Gallery.display_order.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_galleries(self, search_term: str, active_only: bool = True, limit: Optional[int] = None) -> List[Gallery]:
        """Search gallery items by title."""
        filters = [
            Gallery.deleted_at.is_(None),
            Gallery.title.ilike(f"%{search_term}%")
        ]
        
        if active_only:
            filters.append(Gallery.is_active == True)
        
        query = select(Gallery).where(and_(*filters)).order_by(Gallery.display_order.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== ORDERING OPERATIONS =====
    
    async def get_max_display_order(self) -> int:
        """Get the maximum display order."""
        query = select(func.max(Gallery.display_order)).where(
            Gallery.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        max_order = result.scalar()
        return max_order or 0
    
    async def get_items_in_order_range(self, start_order: int, end_order: int) -> List[Gallery]:
        """Get gallery items in a specific order range."""
        query = select(Gallery).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.display_order >= start_order,
                Gallery.display_order <= end_order
            )
        ).order_by(Gallery.display_order.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_item_at_order(self, display_order: int) -> Optional[Gallery]:
        """Get gallery item at specific display order."""
        query = select(Gallery).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.display_order == display_order
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_display_order(self, gallery_id: int, new_order: int, updated_by: Optional[int] = None) -> bool:
        """Update display order for a gallery item."""
        query = (
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                display_order=new_order,
                updated_at=datetime.utcnow(),
                updated_by=updated_by
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def shift_orders_up(self, from_order: int, to_order: int, updated_by: Optional[int] = None) -> int:
        """Shift display orders up (decrease by 1) in a range."""
        query = (
            update(Gallery)
            .where(
                and_(
                    Gallery.deleted_at.is_(None),
                    Gallery.display_order >= from_order,
                    Gallery.display_order <= to_order
                )
            )
            .values(
                display_order=Gallery.display_order - 1,
                updated_at=datetime.utcnow(),
                updated_by=updated_by
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def shift_orders_down(self, from_order: int, to_order: int, updated_by: Optional[int] = None) -> int:
        """Shift display orders down (increase by 1) in a range."""
        query = (
            update(Gallery)
            .where(
                and_(
                    Gallery.deleted_at.is_(None),
                    Gallery.display_order >= from_order,
                    Gallery.display_order <= to_order
                )
            )
            .values(
                display_order=Gallery.display_order + 1,
                updated_at=datetime.utcnow(),
                updated_by=updated_by
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def reorder_items(self, order_mappings: List[Dict[str, int]], updated_by: Optional[int] = None) -> int:
        """Bulk reorder items based on mapping."""
        success_count = 0
        
        # Use a transaction for bulk operations
        try:
            for mapping in order_mappings:
                gallery_id = mapping.get("gallery_id")
                new_order = mapping.get("new_order")
                
                if gallery_id and new_order is not None:
                    query = (
                        update(Gallery)
                        .where(Gallery.id == gallery_id)
                        .values(
                            display_order=new_order,
                            updated_at=datetime.utcnow(),
                            updated_by=updated_by
                        )
                    )
                    result = await self.session.execute(query)
                    if result.rowcount > 0:
                        success_count += 1
            
            await self.session.commit()
            return success_count
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def normalize_orders(self) -> int:
        """Normalize display orders to remove gaps (1, 2, 3, ...)."""
        # Get all active items ordered by current display_order
        query = select(Gallery).where(
            Gallery.deleted_at.is_(None)
        ).order_by(Gallery.display_order.asc(), Gallery.id.asc())
        
        result = await self.session.execute(query)
        galleries = result.scalars().all()
        
        # Update each item with normalized order
        success_count = 0
        for index, gallery in enumerate(galleries, start=1):
            if gallery.display_order != index:
                gallery.display_order = index
                gallery.updated_at = datetime.utcnow()
                success_count += 1
        
        await self.session.commit()
        return success_count
    
    async def get_all_ordered(self) -> List[Gallery]:
        """Get all active gallery items ordered by display_order."""
        query = select(Gallery).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_active == True
            )
        ).order_by(Gallery.display_order.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_active_galleries(self) -> int:
        """Count active gallery items."""
        query = select(func.count(Gallery.id)).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_order_conflicts(self) -> List[Dict[str, Any]]:
        """Get items that have conflicting display orders."""
        query = text("""
            SELECT display_order, COUNT(*) as count, 
                   STRING_AGG(CAST(id AS TEXT), ', ') as gallery_ids
            FROM galleries 
            WHERE deleted_at IS NULL 
            GROUP BY display_order 
            HAVING COUNT(*) > 1
            ORDER BY display_order
        """)
        
        result = await self.session.execute(query)
        conflicts = []
        for row in result:
            conflicts.append({
                "display_order": row.display_order,
                "count": row.count,
                "gallery_ids": row.gallery_ids.split(", ") if row.gallery_ids else []
            })
        
        return conflicts