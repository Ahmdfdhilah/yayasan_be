"""EvaluationAspect service for PKG system."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.evaluation_aspect import EvaluationAspectRepository
from src.repositories.teacher_evaluation import TeacherEvaluationRepository
from src.schemas.evaluation_aspect import (
    EvaluationAspectCreate,
    EvaluationAspectUpdate,
    EvaluationAspectResponse,
    EvaluationAspectListResponse,
    EvaluationAspectSummary,
    EvaluationAspectBulkCreate,
    EvaluationAspectBulkUpdate,
    EvaluationAspectBulkDelete,
    EvaluationAspectAnalytics,
    AspectPerformanceAnalysis,
    EvaluationAspectStats,
    AspectOrderUpdate,
    CategoryAspectsReorder,
    CategoryWithAspectsResponse
)
from src.schemas.evaluation_category import (
    EvaluationCategoryCreate,
    EvaluationCategoryUpdate,
    EvaluationCategoryResponse,
    EvaluationCategoryListResponse,
    EvaluationCategorySummary,
    CategoryOrderUpdate,
    CategoriesReorder,
    EvaluationCategoryFilterParams
)
from src.schemas.evaluation_aspect import EvaluationAspectFilterParams
from src.schemas.shared import MessageResponse
from src.utils.messages import get_message


class EvaluationAspectService:
    """Service for evaluation aspect operations with auto-sync."""
    
    def __init__(self, aspect_repo: EvaluationAspectRepository, evaluation_repo: TeacherEvaluationRepository = None, session: AsyncSession = None):
        self.aspect_repo = aspect_repo
        self.evaluation_repo = evaluation_repo 
        self.session = session 
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create_aspect(self, aspect_data: EvaluationAspectCreate, created_by: Optional[int] = None) -> EvaluationAspectResponse:
        """Create new evaluation aspect with auto-sync."""
        # Validate category exists
        category = await self.aspect_repo.get_category_by_id(aspect_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {aspect_data.category_id} not found"
            )
        
        aspect = await self.aspect_repo.create(aspect_data, created_by)
        
        # If aspect is active, sync to all existing evaluations
        if aspect.is_active:
            items_created = await self.aspect_repo.sync_aspect_to_all_evaluations(aspect.id, created_by)
            if items_created > 0 and self.evaluation_repo:
                await self.evaluation_repo.recalculate_all_aggregates()
           
        
        return EvaluationAspectResponse.from_evaluation_aspect_model(aspect, include_stats=True)
    
    async def get_aspect_by_id(self, aspect_id: int) -> EvaluationAspectResponse:
        """Get evaluation aspect by ID."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aspek evaluasi tidak ditemukan"
            )
        
        # Get statistics
        stats = await self.aspect_repo.get_aspect_statistics(aspect_id)
        
        response = EvaluationAspectResponse.from_evaluation_aspect_model(
            aspect, include_stats=True
        )
        
        # Add statistics
        response.evaluation_count = stats["evaluation_count"]
        
        return response
    
    async def update_aspect(
        self, 
        aspect_id: int, 
        aspect_data: EvaluationAspectUpdate,
        updated_by: Optional[int] = None
    ) -> EvaluationAspectResponse:
        """Update evaluation aspect with auto-sync."""
        # Check if aspect exists
        existing_aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not existing_aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aspek evaluasi tidak ditemukan"
            )
        
        # Check if name change conflicts with existing aspect
        if aspect_data.aspect_name and aspect_data.aspect_name != existing_aspect.aspect_name:
            if await self.aspect_repo.aspect_exists(
                aspect_data.aspect_name,
                exclude_id=aspect_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evaluation aspect '{aspect_data.aspect_name}' already exists"
                )
        
        was_active = existing_aspect.is_active
        updated_aspect = await self.aspect_repo.update(aspect_id, aspect_data, updated_by)
        
        # Handle activation/deactivation synchronization
        if aspect_data.is_active is not None:
            if not was_active and aspect_data.is_active:
                # Aspect was activated - add to all existing evaluations
                items_created = await self.aspect_repo.sync_aspect_to_all_evaluations(aspect_id, updated_by)
                if items_created > 0 and self.evaluation_repo:
                    await self.evaluation_repo.recalculate_all_aggregates()
             
            elif was_active and not aspect_data.is_active:
                # Aspect was deactivated - remove from all evaluations
                items_deleted = await self.aspect_repo.remove_aspect_from_all_evaluations(aspect_id)
                if items_deleted > 0 and self.evaluation_repo:
                    await self.evaluation_repo.recalculate_all_aggregates()
             
        return EvaluationAspectResponse.from_evaluation_aspect_model(updated_aspect, include_stats=True)
    
    async def delete_aspect(self, aspect_id: int) -> MessageResponse:
        """Delete evaluation aspect with auto-sync."""
        # Check if aspect exists
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aspek evaluasi tidak ditemukan"
            )
        
        # Remove from all teacher evaluations first
        items_deleted = await self.aspect_repo.remove_aspect_from_all_evaluations(aspect_id)
        if items_deleted > 0 and self.evaluation_repo:
            await self.evaluation_repo.recalculate_all_aggregates()

        # Then delete the aspect
        success = await self.aspect_repo.soft_delete(aspect_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete evaluation aspect"
            )
        
        return MessageResponse(message="Evaluation aspect deleted and removed from all evaluations")
    
    async def activate_aspect(self, aspect_id: int, activated_by: Optional[int] = None) -> EvaluationAspectResponse:
        """Activate evaluation aspect with auto-sync."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aspek evaluasi tidak ditemukan"
            )
        
        success = await self.aspect_repo.activate(aspect_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate evaluation aspect"
            )
        
        # Sync to all existing evaluations
        items_created = await self.aspect_repo.sync_aspect_to_all_evaluations(aspect_id, activated_by)
        if items_created > 0 and self.evaluation_repo:
            await self.evaluation_repo.recalculate_all_aggregates()
            print(f"✅ Synced activated aspect {aspect_id} to {items_created} evaluations")
        
        updated_aspect = await self.aspect_repo.get_by_id(aspect_id)
        return EvaluationAspectResponse.from_evaluation_aspect_model(
            updated_aspect
        )
    
    async def deactivate_aspect(self, aspect_id: int, deactivated_by: Optional[int] = None) -> EvaluationAspectResponse:
        """Deactivate evaluation aspect with auto-sync."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aspek evaluasi tidak ditemukan"
            )
        
        success = await self.aspect_repo.deactivate(aspect_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate evaluation aspect"
            )
        
        # Remove from all evaluations
        items_deleted = await self.aspect_repo.remove_aspect_from_all_evaluations(aspect_id)
        if items_deleted > 0 and self.evaluation_repo:
            await self.evaluation_repo.recalculate_all_aggregates()
            print(f"✅ Removed deactivated aspect {aspect_id} from {items_deleted} evaluation items")
            
        
        updated_aspect = await self.aspect_repo.get_by_id(aspect_id)
        return EvaluationAspectResponse.from_evaluation_aspect_model(
            updated_aspect
        )
    
    # ===== LISTING AND FILTERING =====
    
    async def get_aspects(self, filters: EvaluationAspectFilterParams) -> EvaluationAspectListResponse:
        """Get evaluation aspects with filters and pagination."""
        aspects, total = await self.aspect_repo.get_all_aspects_filtered(filters)
        
        # Convert to response objects
        aspect_responses = []
        for aspect in aspects:
            # Get statistics if needed
            stats = {}
            if filters.q or hasattr(filters, 'include_stats'):
                stats = await self.aspect_repo.get_aspect_statistics(aspect.id)
            
            response = EvaluationAspectResponse.from_evaluation_aspect_model(
                aspect, include_stats=bool(stats)
            )
            
            if stats:
                response.evaluation_count = stats["evaluation_count"]
                response.avg_score = stats["avg_score"]
            
            aspect_responses.append(response)
        
        return EvaluationAspectListResponse(
            items=aspect_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_active_aspects(self) -> List[EvaluationAspectSummary]:
        """Get all active evaluation aspects."""
        aspects = await self.aspect_repo.get_active_aspects()
        
        return [
            EvaluationAspectSummary.from_evaluation_aspect_model(aspect)
            for aspect in aspects
        ]
    
    async def get_aspects_by_category(
        self, 
        category_id: int
    ) -> List[EvaluationAspectSummary]:
        """Get aspects by category ID."""
        aspects = await self.aspect_repo.get_aspects_by_category(category_id)
        
        return [
            EvaluationAspectSummary.from_evaluation_aspect_model(aspect)
            for aspect in aspects
        ]
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_create_aspects(self, bulk_data: EvaluationAspectBulkCreate, created_by: Optional[int] = None) -> List[EvaluationAspectResponse]:
        """Bulk create evaluation aspects."""
        # Validate unique names within the batch
        aspect_names = [aspect.aspect_name for aspect in bulk_data.aspects]
        if len(aspect_names) != len(set(aspect_names)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate aspect names found in bulk creation request"
            )
        
        # Check for existing names
        for aspect_data in bulk_data.aspects:
            if await self.aspect_repo.aspect_exists(aspect_data.aspect_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evaluation aspect '{aspect_data.aspect_name}' already exists"
                )
        
        aspects = await self.aspect_repo.bulk_create(bulk_data.aspects, created_by)
        
        return [
            EvaluationAspectResponse.from_evaluation_aspect_model(aspect, include_stats=True)
            for aspect in aspects
        ]
    
    async def bulk_update_aspects(self, bulk_data: EvaluationAspectBulkUpdate) -> Dict[str, Any]:
        """Bulk update evaluation aspects."""
        # Validate aspect IDs exist
        for aspect_id in bulk_data.aspect_ids:
            aspect = await self.aspect_repo.get_by_id(aspect_id)
            if not aspect:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evaluation aspect with ID {aspect_id} not found"
                )
        
        updated_count = 0
        
        if bulk_data.is_active is not None:
            updated_count = await self.aspect_repo.bulk_update_status(
                bulk_data.aspect_ids,
                bulk_data.is_active
            )
        
        return {
            "message": f"Successfully updated {updated_count} evaluation aspects",
            "updated_count": updated_count
        }
    
    async def bulk_delete_aspects(self, bulk_data: EvaluationAspectBulkDelete) -> Dict[str, Any]:
        """Bulk delete evaluation aspects."""
        deleted_count = 0
        errors = []
        
        for aspect_id in bulk_data.aspect_ids:
            try:
                aspect = await self.aspect_repo.get_by_id(aspect_id)
                if not aspect:
                    errors.append(f"Aspect {aspect_id} not found")
                    continue
                
                # Check if aspect has evaluations
                if not bulk_data.force_delete and await self.aspect_repo.has_evaluations(aspect_id):
                    errors.append(f"Aspect {aspect_id} has existing evaluations")
                    continue
                
                success = await self.aspect_repo.soft_delete(aspect_id)
                if success:
                    deleted_count += 1
                else:
                    errors.append(f"Failed to delete aspect {aspect_id}")
                    
            except Exception as e:
                errors.append(f"Error deleting aspect {aspect_id}: {str(e)}")
        
        return {
            "message": f"Deleted {deleted_count} evaluation aspects",
            "deleted_count": deleted_count,
            "errors": errors
        }
    
    
    # ===== ANALYTICS =====
    
    async def get_aspects_analytics(self) -> EvaluationAspectAnalytics:
        """Get comprehensive aspects analytics."""
        analytics_data = await self.aspect_repo.get_aspects_analytics()
        
        # Get most/least used aspects
        aspects = await self.aspect_repo.get_active_aspects()
        most_used = []
        least_used = []
        avg_grades = {}
        
        for aspect in aspects[:10]:  # Limit to top 10
            stats = await self.aspect_repo.get_aspect_statistics(aspect.id)
            
            aspect_info = {
                "aspect_id": aspect.id,
                "aspect_name": aspect.aspect_name,
                "evaluation_count": stats["evaluation_count"],
                "avg_score": stats.get("avg_score", 0)
            }
            
            if stats["evaluation_count"] > 0:
                most_used.append(aspect_info)
                avg_grades[aspect.aspect_name] = stats.get("avg_grade", "C")
            else:
                least_used.append(aspect_info)
        
        # Sort by usage
        most_used.sort(key=lambda x: x["evaluation_count"], reverse=True)
        least_used.sort(key=lambda x: x["evaluation_count"])
        
        return EvaluationAspectAnalytics(
            total_aspects=analytics_data["total_aspects"],
            active_aspects=analytics_data["active_aspects"],
            inactive_aspects=analytics_data["inactive_aspects"],
            most_used_aspects=most_used[:5],
            least_used_aspects=least_used[:5],
            avg_grade_by_aspect=avg_grades
        )
    
    
    async def get_comprehensive_stats(self) -> EvaluationAspectStats:
        """Get comprehensive evaluation aspect statistics."""
        # Get main analytics
        analytics = await self.get_aspects_analytics()
        
        # Get basic performance data for active aspects
        active_aspects = await self.aspect_repo.get_active_aspects()
        aspect_performance = []
        
        for aspect in active_aspects[:10]:  # Limit to prevent overload
            try:
                stats = await self.aspect_repo.get_aspect_statistics(aspect.id)
                
                performance = AspectPerformanceAnalysis(
                    aspect_id=aspect.id,
                    aspect_name=aspect.aspect_name,
                    total_evaluations=stats["evaluation_count"],
                    avg_grade="C",  # Default, would need grade calculation
                    grade_distribution={},  # Would need grade distribution logic
                    trend_data=[],  # Would need time-series data
                    top_performers=[],  # Would need teacher performance data
                    improvement_needed=[]  # Would need teacher performance data
                )
                aspect_performance.append(performance)
            except Exception:
                continue  # Skip aspects with issues
        
        # Generate recommendations
        recommendations = []
        
        if analytics.inactive_aspects > 0:
            recommendations.append(f"Review {analytics.inactive_aspects} inactive aspects")
        
        if len([a for a in analytics.most_used_aspects if a["evaluation_count"] == 0]) > 0:
            recommendations.append("Some aspects have never been used in evaluations")
        
        return EvaluationAspectStats(
            summary=analytics,
            aspect_performance=aspect_performance,
            usage_trends={},  # Would need historical data
            recommendations=recommendations
        )
    
    # ===== SYNC METHODS =====
    
    async def sync_all_active_aspects(self) -> MessageResponse:
        """Manual sync - ensure all active aspects are in all evaluations."""
        
        total_items_created = await self.aspect_repo.sync_all_active_aspects_to_evaluations()
        
        if total_items_created > 0 and self.evaluation_repo:
            await self.evaluation_repo.recalculate_all_aggregates()
        
        return MessageResponse(
            message=f"Manual sync completed. Created {total_items_created} missing evaluation items."
        )
    
    # ===== CATEGORY MANAGEMENT METHODS =====
    
    async def create_category(self, category_data: EvaluationCategoryCreate, created_by: Optional[int] = None) -> EvaluationCategoryResponse:
        """Create new evaluation category."""
        # Check if category name already exists
        categories = await self.aspect_repo.get_all_categories(include_inactive=True)
        if any(cat.name.lower() == category_data.name.lower() for cat in categories):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.name}' already exists"
            )
        
        category = await self.aspect_repo.create_category(
            name=category_data.name,
            description=category_data.description,
            display_order=category_data.display_order,
            created_by=created_by
        )
        
        return EvaluationCategoryResponse.from_evaluation_category_model(category, include_stats=True)
    
    async def update_category(self, category_id: int, category_data: EvaluationCategoryUpdate, updated_by: int) -> EvaluationCategoryResponse:
        """Update an evaluation category."""
        # Check if category exists
        category = await self.aspect_repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check for duplicate name if name is being updated
        if category_data.name and category_data.name != category.name:
            existing_category = await self.aspect_repo.get_category_by_name(category_data.name)
            if existing_category and existing_category.id != category_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Category with this name already exists"
                )
        
        # Update category
        updated_category = await self.aspect_repo.update_category(category_id, category_data, updated_by)
        if not updated_category:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update category"
            )
        
        return EvaluationCategoryResponse.from_evaluation_category_model(updated_category, include_stats=True)
    
    async def get_all_categories(self, include_inactive: bool = False) -> List[EvaluationCategorySummary]:
        """Get all evaluation categories."""
        categories = await self.aspect_repo.get_all_categories(include_inactive)
        
        return [
            EvaluationCategorySummary.from_evaluation_category_model(category)
            for category in categories
        ]
    
    async def update_category_order(self, order_data: CategoryOrderUpdate) -> MessageResponse:
        """Update category display order with automatic gap fixing."""
        # Check if category exists
        category = await self.aspect_repo.get_category_by_id(order_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Access the name before any update operations to avoid lazy loading issues
        category_name = category.name
        
        success = await self.aspect_repo.update_category_order(
            order_data.category_id, 
            order_data.new_order
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update category order"
            )
        
        # Automatically fix any gaps after the update
        await self.aspect_repo.fix_category_ordering_gaps()
        
        return MessageResponse(
            message=f"Successfully updated category '{category_name}' order to {order_data.new_order}"
        )
    
    # ===== ORDERING METHODS =====
    
    async def update_aspect_order(self, order_data: AspectOrderUpdate) -> MessageResponse:
        """Update aspect order with automatic gap fixing."""
        # Check if aspect exists
        aspect = await self.aspect_repo.get_by_id(order_data.aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aspek evaluasi tidak ditemukan"
            )
        
        success = await self.aspect_repo.update_aspect_order(
            order_data.aspect_id, 
            order_data.new_order
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update aspect order"
            )
        
        # Automatically fix any gaps within the category after the update
        await self.aspect_repo.fix_aspect_ordering_gaps_in_category(aspect.category_id)
        
        return MessageResponse(
            message=f"Successfully updated aspect order for '{aspect.aspect_name}' to {order_data.new_order}"
        )
    
    async def reorder_aspects_in_category(self, reorder_data: CategoryAspectsReorder) -> MessageResponse:
        """Reorder multiple aspects within a category with automatic gap fixing."""
        # Check if category exists
        category = await self.aspect_repo.get_category_by_id(reorder_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {reorder_data.category_id} not found"
            )
        
        # Validate that all aspect IDs belong to the specified category
        for aspect_id in reorder_data.aspect_orders.keys():
            aspect = await self.aspect_repo.get_by_id(aspect_id)
            if not aspect:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Aspect with ID {aspect_id} not found"
                )
            if aspect.category_id != reorder_data.category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Aspect {aspect_id} does not belong to category '{category.name}'"
                )
        
        success = await self.aspect_repo.reorder_aspects_in_category(
            reorder_data.category_id, 
            reorder_data.aspect_orders
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reorder aspects in category"
            )
        
        # Automatically fix any gaps after bulk reordering
        await self.aspect_repo.fix_aspect_ordering_gaps_in_category(reorder_data.category_id)
        
        return MessageResponse(
            message=f"Successfully reordered {len(reorder_data.aspect_orders)} aspects in category '{category.name}'"
        )
    
    async def get_categories_with_order(self) -> List[EvaluationCategoryResponse]:
        """Get all categories with their order information and stats."""
        categories_data = await self.aspect_repo.get_categories_with_order()
        
        categories = []
        for category_data in categories_data:
            # Create category response with stats
            category_response = EvaluationCategoryResponse(
                id=category_data['id'],
                name=category_data['name'],
                description=None,  # Would need to fetch from database if needed
                display_order=category_data['display_order'],
                is_active=category_data['is_active'],
                created_at=datetime.now(),  # Would need to fetch from database
                updated_at=None,
                aspects_count=category_data['aspect_count'],
                active_aspects_count=category_data['active_aspects_count']
            )
            categories.append(category_response)
        
        return categories
    
    async def get_aspects_by_category_ordered(self, category_id: int) -> List[EvaluationAspectResponse]:
        """Get aspects by category with proper ordering."""
        aspects = await self.aspect_repo.get_aspects_by_category_ordered(category_id)
        
        return [
            EvaluationAspectResponse.from_evaluation_aspect_model(aspect)
            for aspect in aspects
        ]
    
    async def get_category_with_aspects(self, category_id: int) -> CategoryWithAspectsResponse:
        """Get category with all its aspects."""
        category = await self.aspect_repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        
        aspects = await self.aspect_repo.get_aspects_by_category_ordered(category_id)
        
        return CategoryWithAspectsResponse(
            id=category.id,
            name=category.name,
            display_order=category.display_order,
            is_active=category.is_active,
            aspects=[
                EvaluationAspectResponse.from_evaluation_aspect_model(aspect)
                for aspect in aspects
            ]
        )
    
    async def auto_assign_orders(self) -> MessageResponse:
        """Auto-assign orders to categories and aspects with automatic gap fixing."""
        success = await self.aspect_repo.auto_assign_orders()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to auto-assign orders"
            )
        
        # Automatically fix gaps after auto-assignment
        await self.aspect_repo.fix_category_ordering_gaps()
        
        # Fix aspect ordering gaps for all categories
        categories = await self.aspect_repo.get_all_categories(include_inactive=True)
        for category in categories:
            await self.aspect_repo.fix_aspect_ordering_gaps_in_category(category.id)
        
        return MessageResponse(
            message="Successfully auto-assigned orders to all categories and aspects"
        )
    
