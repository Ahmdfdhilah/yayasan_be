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
            is_highlight=gallery_data.is_highlight,
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
        
        if filters.is_highlighted is not None:
            highlight_filter = Gallery.is_highlight == filters.is_highlighted
            query = query.where(highlight_filter)
            count_query = count_query.where(highlight_filter)
        
        
        # Apply sorting
        if filters.sort_by == "title":
            sort_column = Gallery.title
        elif filters.sort_by == "created_at":
            sort_column = Gallery.created_at
        elif filters.sort_by == "updated_at":
            sort_column = Gallery.updated_at
        elif filters.sort_by == "is_highlight":
            sort_column = Gallery.is_highlight
        else:
            sort_column = Gallery.created_at
        
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
    
    async def get_all_galleries(self, limit: Optional[int] = None) -> List[Gallery]:
        """Get all gallery items."""
        query = select(Gallery).where(
            Gallery.deleted_at.is_(None)
        ).order_by(Gallery.is_highlight.desc(), Gallery.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_galleries(self, search_term: str, limit: Optional[int] = None) -> List[Gallery]:
        """Search gallery items by title."""
        filters = [
            Gallery.deleted_at.is_(None),
            Gallery.title.ilike(f"%{search_term}%")
        ]
        
        
        query = select(Gallery).where(and_(*filters)).order_by(Gallery.is_highlight.desc(), Gallery.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== HIGHLIGHT OPERATIONS =====
    
    async def get_highlighted_galleries(self, limit: Optional[int] = None) -> List[Gallery]:
        """Get all highlighted gallery items."""
        query = select(Gallery).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_highlight == True
            )
        ).order_by(Gallery.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_non_highlighted_galleries(self, limit: Optional[int] = None) -> List[Gallery]:
        """Get all non-highlighted gallery items."""
        query = select(Gallery).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_highlight == False
            )
        ).order_by(Gallery.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_highlighted_galleries(self) -> int:
        """Count highlighted gallery items."""
        query = select(func.count(Gallery.id)).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_highlight == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def count_all_galleries(self) -> int:
        """Count all gallery items."""
        query = select(func.count(Gallery.id)).where(
            Gallery.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_gallery_statistics(self) -> Dict[str, Any]:
        """Get gallery statistics including highlight counts."""
        total_query = select(func.count(Gallery.id)).where(Gallery.deleted_at.is_(None))
        highlighted_query = select(func.count(Gallery.id)).where(
            and_(
                Gallery.deleted_at.is_(None),
                Gallery.is_highlight == True
            )
        )
        
        total_result = await self.session.execute(total_query)
        highlighted_result = await self.session.execute(highlighted_query)
        
        total_count = total_result.scalar() or 0
        highlighted_count = highlighted_result.scalar() or 0
        
        return {
            "total_galleries": total_count,
            "highlighted_galleries": highlighted_count,
            "non_highlighted_galleries": total_count - highlighted_count
        }