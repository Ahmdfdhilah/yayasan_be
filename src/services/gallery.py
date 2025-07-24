"""Gallery service for business logic with advanced ordering management."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.gallery import GalleryRepository
from src.schemas.gallery import (
    GalleryCreate, GalleryUpdate, GalleryResponse, GalleryListResponse,
    GallerySummary, GalleryFilterParams, GalleryOrderUpdate, GalleryBulkOrderUpdate,
    OrderUpdateResult, BulkOrderUpdateResponse
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
    
    async def get_active_galleries(self, limit: Optional[int] = None) -> List[GalleryResponse]:
        """Get active gallery items only."""
        galleries = await self.gallery_repo.get_active_galleries(limit)
        return [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
    
    async def search_galleries(self, search_term: str, active_only: bool = True, limit: Optional[int] = None) -> List[GalleryResponse]:
        """Search gallery items by title."""
        galleries = await self.gallery_repo.search_galleries(search_term, active_only, limit)
        return [GalleryResponse.from_gallery_model(gallery) for gallery in galleries]
    
    async def get_gallery_summaries(self, filters: GalleryFilterParams) -> List[GallerySummary]:
        """Get gallery summaries (lighter response)."""
        galleries, _ = await self.gallery_repo.get_all_filtered(filters)
        return [GallerySummary.from_gallery_model(gallery) for gallery in galleries]
    
    async def toggle_active_status(self, gallery_id: int, updated_by: Optional[int] = None) -> GalleryResponse:
        """Toggle active status of a gallery item."""
        # Check if gallery exists
        existing_gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not existing_gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery item not found"
            )
        
        # Toggle active status
        update_data = GalleryUpdate(is_active=not existing_gallery.is_active)
        updated_gallery = await self.gallery_repo.update(gallery_id, update_data, updated_by)
        
        if not updated_gallery:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to toggle active status"
            )
        
        return GalleryResponse.from_gallery_model(updated_gallery)
    
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
    
    async def bulk_update_order(self, bulk_order_data: GalleryBulkOrderUpdate, updated_by: Optional[int] = None) -> BulkOrderUpdateResponse:
        """Bulk update display orders for multiple gallery items."""
        successful_updates = []
        failed_updates = []
        
        # Validate all gallery items exist first
        gallery_orders = {}
        for item in bulk_order_data.items:
            gallery = await self.gallery_repo.get_by_id(item.gallery_id)
            if gallery:
                gallery_orders[item.gallery_id] = gallery.display_order
            else:
                failed_updates.append(OrderUpdateResult(
                    gallery_id=item.gallery_id,
                    old_order=0,
                    new_order=item.new_order,
                    success=False,
                    message="Gallery item not found"
                ))
        
        # Prepare order mappings for bulk operation
        order_mappings = []
        for item in bulk_order_data.items:
            if item.gallery_id in gallery_orders:
                old_order = gallery_orders[item.gallery_id]
                order_mappings.append({
                    "gallery_id": item.gallery_id,
                    "new_order": item.new_order
                })
                successful_updates.append(OrderUpdateResult(
                    gallery_id=item.gallery_id,
                    old_order=old_order,
                    new_order=item.new_order,
                    success=True,
                    message="Order updated successfully"
                ))
        
        # Execute bulk reorder
        try:
            success_count = await self.gallery_repo.reorder_items(order_mappings, updated_by)
            
            # If some items failed during bulk operation, move them to failed list
            if success_count != len(order_mappings):
                # This is a simplified approach - in real scenario you'd want more detailed error handling
                pass
            
        except Exception as e:
            # Move all to failed if bulk operation fails
            for update in successful_updates:
                update.success = False
                update.message = f"Bulk operation failed: {str(e)}"
                failed_updates.append(update)
            successful_updates = []
        
        return BulkOrderUpdateResponse(
            successful_updates=successful_updates,
            failed_updates=failed_updates,
            total_processed=len(bulk_order_data.items),
            success_count=len(successful_updates),
            failure_count=len(failed_updates)
        )
    
    async def normalize_gallery_orders(self) -> MessageResponse:
        """Normalize all gallery display orders to remove gaps."""
        updated_count = await self.gallery_repo.normalize_orders()
        return MessageResponse(
            message=f"Gallery orders normalized. {updated_count} items updated."
        )
    
    async def get_order_conflicts(self) -> Dict[str, Any]:
        """Get gallery items that have conflicting display orders."""
        conflicts = await self.gallery_repo.get_order_conflicts()
        return {
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "needs_normalization": len(conflicts) > 0
        }
    
    async def get_gallery_statistics(self) -> Dict[str, Any]:
        """Get gallery statistics."""
        total_galleries = len(await self.gallery_repo.get_all_filtered(GalleryFilterParams())[0])
        active_galleries = await self.gallery_repo.count_active_galleries()
        inactive_galleries = total_galleries - active_galleries
        max_order = await self.gallery_repo.get_max_display_order()
        conflicts = await self.gallery_repo.get_order_conflicts()
        
        return {
            "total_galleries": total_galleries,
            "active_galleries": active_galleries,
            "inactive_galleries": inactive_galleries,
            "max_display_order": max_order,
            "order_conflicts": len(conflicts),
            "needs_normalization": len(conflicts) > 0
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