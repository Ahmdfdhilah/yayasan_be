"""Gallery service for business logic with advanced ordering management."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.gallery import GalleryRepository
from src.schemas.gallery import (
    GalleryCreate, GalleryUpdate, GalleryResponse, GalleryListResponse,
    GallerySummary, GalleryFilterParams
)
from src.schemas.shared import MessageResponse


class GalleryService:
    """Gallery service for business logic with advanced ordering management."""
    
    def __init__(self, gallery_repo: GalleryRepository):
        self.gallery_repo = gallery_repo
    
    async def create_gallery(self, gallery_data: GalleryCreate, created_by: Optional[int] = None) -> GalleryResponse:
        """Create a new gallery item."""
        # Create gallery item in database
        gallery = await self.gallery_repo.create(gallery_data, created_by)
        
        return GalleryResponse.from_gallery_model(gallery)
    
    async def get_gallery(self, gallery_id: int) -> GalleryResponse:
        """Get gallery item by ID."""
        gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery item not found"
            )
        
        return GalleryResponse.from_gallery_model(gallery)
    
    async def update_gallery(self, gallery_id: int, gallery_data: GalleryUpdate, updated_by: Optional[int] = None) -> GalleryResponse:
        """Update gallery item information."""
        # Check if gallery exists
        existing_gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not existing_gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery item not found"
            )
        
        # Update gallery in database
        updated_gallery = await self.gallery_repo.update(gallery_id, gallery_data, updated_by)
        if not updated_gallery:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update gallery item"
            )
        
        return GalleryResponse.from_gallery_model(updated_gallery)
    
    async def delete_gallery(self, gallery_id: int, deleted_by: Optional[int] = None) -> MessageResponse:
        """Delete gallery item (soft delete)."""
        # Check if gallery exists
        existing_gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not existing_gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery item not found"
            )
        
        # Soft delete gallery
        success = await self.gallery_repo.soft_delete(gallery_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete gallery item"
            )
        
        return MessageResponse(message="Gallery item deleted successfully")
    
    async def get_galleries(self, filters: GalleryFilterParams) -> GalleryListResponse:
        """Get galleries with filters and pagination."""
        galleries, total = await self.gallery_repo.get_all_filtered(filters)
        
        gallery_responses = [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
        
        return GalleryListResponse(
            items=gallery_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_all_galleries(self, limit: Optional[int] = None) -> List[GalleryResponse]:
        """Get all gallery items."""
        galleries = await self.gallery_repo.get_all_galleries(limit)
        return [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
    
    async def search_galleries(self, search_term: str, limit: Optional[int] = None) -> List[GalleryResponse]:
        """Search gallery items by title."""
        galleries = await self.gallery_repo.search_galleries(search_term, limit)
        return [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
    
    async def get_gallery_summaries(self, filters: GalleryFilterParams) -> List[GallerySummary]:
        """Get gallery summaries (lighter response)."""
        galleries, _ = await self.gallery_repo.get_all_filtered(filters)
        return [GallerySummary.from_gallery_model(gallery) for gallery in galleries]
    
    
    # ===== HIGHLIGHT OPERATIONS =====
    
    async def get_highlighted_galleries(self, limit: Optional[int] = None) -> List[GalleryResponse]:
        """Get all highlighted gallery items."""
        galleries = await self.gallery_repo.get_highlighted_galleries(limit)
        return [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
    
    async def get_non_highlighted_galleries(self, limit: Optional[int] = None) -> List[GalleryResponse]:
        """Get all non-highlighted gallery items."""
        galleries = await self.gallery_repo.get_non_highlighted_galleries(limit)
        return [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
    
    
    async def get_gallery_statistics(self) -> Dict[str, Any]:
        """Get gallery statistics."""
        return await self.gallery_repo.get_gallery_statistics()
    
