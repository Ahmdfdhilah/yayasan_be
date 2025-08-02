"""Mitra business logic services."""

from typing import List, Optional
from fastapi import HTTPException, status

from src.repositories.mitra import MitraRepository
from src.schemas.mitra import MitraCreate, MitraUpdate, MitraResponse, MitraListResponse, MitraFilterParams
from src.schemas.shared import MessageResponse


class MitraService:
    """Service for mitra business logic."""

    def __init__(self, mitra_repo: MitraRepository):
        self.mitra_repo = mitra_repo

    async def create_mitra(self, mitra_data: MitraCreate) -> MitraResponse:
        """Create a new mitra."""
        # Check if title already exists
        existing = await self.mitra_repo.get_by_title(mitra_data.title)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mitra with this title already exists"
            )
        
        mitra = await self.mitra_repo.create(mitra_data)
        return MitraResponse.model_validate(mitra)

    async def get_mitra(self, mitra_id: int) -> MitraResponse:
        """Get mitra by ID."""
        mitra = await self.mitra_repo.get_by_id(mitra_id)
        if not mitra:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mitra not found"
            )
        
        return MitraResponse.model_validate(mitra)

    async def get_all_mitras(
        self,
        filters: MitraFilterParams
    ) -> MitraListResponse:
        """Get all mitras with pagination and search."""
        mitras, total = await self.mitra_repo.get_all(
            skip=filters.skip,
            limit=filters.limit,
            search=filters.search
        )
        
        return MitraListResponse(
            items=[MitraResponse.model_validate(mitra) for mitra in mitras],
            total=total,
            page=(filters.skip // filters.limit) + 1,
            size=filters.limit,
            pages=(total + filters.limit - 1) // filters.limit
        )

    async def update_mitra(
        self, 
        mitra_id: int, 
        update_data: MitraUpdate
    ) -> MitraResponse:
        """Update mitra."""
        # Check if mitra exists
        existing = await self.mitra_repo.get_by_id(mitra_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mitra not found"
            )
        
        # Check if new title conflicts with another mitra
        if update_data.title and update_data.title != existing.title:
            title_conflict = await self.mitra_repo.get_by_title(update_data.title)
            if title_conflict and title_conflict.id != mitra_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mitra with this title already exists"
                )
        
        updated_mitra = await self.mitra_repo.update(mitra_id, update_data)
        return MitraResponse.model_validate(updated_mitra)

    async def delete_mitra(self, mitra_id: int) -> MessageResponse:
        """Delete mitra."""
        # Check if mitra exists
        existing = await self.mitra_repo.get_by_id(mitra_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mitra not found"
            )
        
        deleted = await self.mitra_repo.delete(mitra_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete mitra"
            )
        
        return MessageResponse(message="Mitra deleted successfully")