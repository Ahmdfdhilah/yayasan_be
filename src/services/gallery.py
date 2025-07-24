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
        # If no display_order specified, set to next available
        if gallery_data.display_order == 0:
            max_order = await self.gallery_repo.get_max_display_order()
            gallery_data.display_order = max_order + 1
        else:
            # Handle position insertion - shift existing items
            await self._handle_order_insertion(gallery_data.display_order, created_by)
        
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
        
        # Handle display order change if specified
        if gallery_data.display_order is not None and gallery_data.display_order != existing_gallery.display_order:
            await self._handle_order_change(gallery_id, existing_gallery.display_order, gallery_data.display_order, updated_by)
            # Remove display_order from update data as it's handled separately
            gallery_data.display_order = None
        
        # Update gallery in database
        updated_gallery = await self.gallery_repo.update(gallery_id, gallery_data, updated_by)
        if not updated_gallery:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update gallery item"
            )
        
        return GalleryResponse.from_gallery_model(updated_gallery)
    
    async def delete_gallery(self, gallery_id: int, deleted_by: Optional[int] = None) -> MessageResponse:
        """Delete gallery item (soft delete) and handle order gaps."""
        # Check if gallery exists and get its order
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
        
        # Shift items after deleted item up to close the gap
        max_order = await self.gallery_repo.get_max_display_order()
        if existing_gallery.display_order < max_order:
            await self.gallery_repo.shift_orders_up(
                existing_gallery.display_order + 1, 
                max_order, 
                deleted_by
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
    
    
    # ===== ADVANCED ORDERING OPERATIONS =====
    
    async def update_single_order(self, gallery_id: int, new_order: int, updated_by: Optional[int] = None) -> GalleryResponse:
        """Update display order for a single gallery item."""
        # Check if gallery exists
        existing_gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not existing_gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery item not found"
            )
        
        old_order = existing_gallery.display_order
        if old_order == new_order:
            return GalleryResponse.from_gallery_model(existing_gallery)
        
        # Handle the order change
        await self._handle_order_change(gallery_id, old_order, new_order, updated_by)
        
        # Return updated gallery
        updated_gallery = await self.gallery_repo.get_by_id(gallery_id)
        return GalleryResponse.from_gallery_model(updated_gallery)
    
    
    async def get_gallery_statistics(self) -> Dict[str, Any]:
        """Get gallery statistics."""
        galleries, total_count = await self.gallery_repo.get_all_filtered(GalleryFilterParams())
        
        return {
            "total_galleries": total_count
        }
    
    # ===== PRIVATE HELPER METHODS =====
    
    async def _handle_order_insertion(self, new_order: int, updated_by: Optional[int] = None):
        """Handle insertion of new item at specific order position."""
        # Check if position is occupied
        existing_item = await self.gallery_repo.get_item_at_order(new_order)
        if existing_item:
            # Shift all items from this position downward
            max_order = await self.gallery_repo.get_max_display_order()
            await self.gallery_repo.shift_orders_down(new_order, max_order, updated_by)
    
    async def _handle_order_change(self, gallery_id: int, old_order: int, new_order: int, updated_by: Optional[int] = None):
        """Handle order change for existing item."""
        if old_order == new_order:
            return
        
        if new_order > old_order:
            # Moving down: shift items in between up
            await self.gallery_repo.shift_orders_up(old_order + 1, new_order, updated_by)
        else:
            # Moving up: shift items in between down
            await self.gallery_repo.shift_orders_down(new_order, old_order - 1, updated_by)
        
        # Update the item's order
        await self.gallery_repo.update_display_order(gallery_id, new_order, updated_by)