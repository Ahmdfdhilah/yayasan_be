"""Mitra repository for database operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update

from src.models.mitra import Mitra
from src.schemas.mitra import MitraCreate, MitraUpdate


class MitraRepository:
    """Repository for mitra operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, mitra_data: MitraCreate) -> Mitra:
        """Create a new mitra."""
        mitra = Mitra(**mitra_data.dict())
        self.session.add(mitra)
        await self.session.commit()
        await self.session.refresh(mitra)
        return mitra

    async def get_by_id(self, mitra_id: int) -> Optional[Mitra]:
        """Get mitra by ID."""
        query = select(Mitra).where(Mitra.id == mitra_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[Mitra], int]:
        """Get all mitras with pagination and search."""
        query = select(Mitra)
        count_query = select(func.count(Mitra.id))
        
        # Apply search filter
        if search:
            search_filter = or_(
                Mitra.title.ilike(f"%{search}%"),
                Mitra.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        mitras = result.scalars().all()
        
        return list(mitras), total

    async def update(self, mitra_id: int, update_data: MitraUpdate) -> Optional[Mitra]:
        """Update mitra."""
        # Get existing mitra
        mitra = await self.get_by_id(mitra_id)
        if not mitra:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(mitra, field, value)
        
        await self.session.commit()
        await self.session.refresh(mitra)
        return mitra

    async def delete(self, mitra_id: int) -> bool:
        """Delete mitra."""
        query = delete(Mitra).where(Mitra.id == mitra_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def get_by_title(self, title: str) -> Optional[Mitra]:
        """Get mitra by title."""
        query = select(Mitra).where(Mitra.title == title)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()