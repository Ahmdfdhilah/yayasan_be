"""EvaluationAspect service for PKG system."""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.evaluation_aspect import EvaluationAspectRepository
from src.schemas.evaluation_aspect import (
    EvaluationAspectCreate,
    EvaluationAspectUpdate,
    EvaluationAspectResponse,
    EvaluationAspectListResponse,
    EvaluationAspectSummary,
    EvaluationAspectBulkCreate,
    EvaluationAspectBulkUpdate,
    EvaluationAspectBulkDelete,
    WeightValidation,
    WeightValidationResponse,
    EvaluationAspectAnalytics,
    AspectPerformanceAnalysis,
    EvaluationAspectStats
)
from src.schemas.filters import EvaluationAspectFilterParams


class EvaluationAspectService:
    """Service for evaluation aspect operations."""
    
    def __init__(self, aspect_repo: EvaluationAspectRepository):
        self.aspect_repo = aspect_repo
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create_aspect(self, aspect_data: EvaluationAspectCreate) -> EvaluationAspectResponse:
        """Create new evaluation aspect."""
        # Check if aspect name already exists
        if await self.aspect_repo.aspect_exists(aspect_data.aspect_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evaluation aspect '{aspect_data.aspect_name}' already exists"
            )
        
        aspect = await self.aspect_repo.create(aspect_data)
        return EvaluationAspectResponse.from_evaluation_aspect_model(aspect, include_stats=True)
    
    async def get_aspect_by_id(self, aspect_id: int) -> EvaluationAspectResponse:
        """Get evaluation aspect by ID."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        # Get statistics
        stats = await self.aspect_repo.get_aspect_statistics(aspect_id)
        
        response = EvaluationAspectResponse.from_evaluation_aspect_model(
            aspect, include_stats=True
        )
        
        # Add statistics
        response.evaluation_count = stats["evaluation_count"]
        response.avg_score = stats["avg_score"]
        
        return response
    
    async def update_aspect(
        self, 
        aspect_id: int, 
        aspect_data: EvaluationAspectUpdate
    ) -> EvaluationAspectResponse:
        """Update evaluation aspect."""
        # Check if aspect exists
        existing_aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not existing_aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
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
        
        updated_aspect = await self.aspect_repo.update(aspect_id, aspect_data)
        return EvaluationAspectResponse.from_evaluation_aspect_model(updated_aspect, include_stats=True)
    
    async def delete_aspect(self, aspect_id: int, force: bool = False) -> Dict[str, str]:
        """Delete evaluation aspect."""
        # Check if aspect exists
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        # Check if aspect has evaluations
        if not force and await self.aspect_repo.has_evaluations(aspect_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete aspect with existing evaluations. Use force=true to override."
            )
        
        success = await self.aspect_repo.soft_delete(aspect_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete evaluation aspect"
            )
        
        return {"message": "Evaluation aspect deleted successfully"}
    
    async def activate_aspect(self, aspect_id: int) -> EvaluationAspectResponse:
        """Activate evaluation aspect."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        success = await self.aspect_repo.activate(aspect_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate evaluation aspect"
            )
        
        updated_aspect = await self.aspect_repo.get_by_id(aspect_id)
        return EvaluationAspectResponse.from_evaluation_aspect_model(
            updated_aspect
        )
    
    async def deactivate_aspect(self, aspect_id: int) -> EvaluationAspectResponse:
        """Deactivate evaluation aspect."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        success = await self.aspect_repo.deactivate(aspect_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate evaluation aspect"
            )
        
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
        category: str
    ) -> List[EvaluationAspectSummary]:
        """Get aspects by category."""
        aspects = await self.aspect_repo.get_aspects_by_category(category)
        
        return [
            EvaluationAspectSummary.from_evaluation_aspect_model(aspect)
            for aspect in aspects
        ]
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_create_aspects(self, bulk_data: EvaluationAspectBulkCreate) -> List[EvaluationAspectResponse]:
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
        
        aspects = await self.aspect_repo.bulk_create(bulk_data.aspects)
        
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
    
    # ===== WEIGHT VALIDATION =====
    
    async def validate_weights(self, validation_data: WeightValidation) -> WeightValidationResponse:
        """Validate aspect weights."""
        # Get aspects
        errors = []
        warnings = []
        total_weight = 0
        
        for aspect_id, weight in validation_data.aspect_weights.items():
            aspect = await self.aspect_repo.get_by_id(aspect_id)
            if not aspect:
                errors.append(f"Aspect with ID {aspect_id} not found")
                continue
            
            # Note: All aspects are now universal across organizations
            
            if weight < 0 or weight > 100:
                errors.append(f"Weight for aspect {aspect_id} must be between 0 and 100")
                continue
            
            total_weight += weight
        
        # Check total weight
        expected_weight = 100
        is_valid = len(errors) == 0 and total_weight == expected_weight
        
        if total_weight > expected_weight:
            errors.append(f"Total weight ({total_weight}%) exceeds 100%")
        elif total_weight < expected_weight:
            warnings.append(f"Total weight ({total_weight}%) is less than 100%")
        
        return WeightValidationResponse(
            is_valid=is_valid,
            total_weight=total_weight,
            errors=errors,
            warnings=warnings
        )
    
    async def validate_all_weights(self) -> WeightValidationResponse:
        """Validate weights for all active aspects."""
        validation_result = await self.aspect_repo.validate_aspect_weights()
        
        return WeightValidationResponse(
            is_valid=validation_result["is_valid"],
            total_weight=validation_result["total_weight"],
            errors=validation_result["errors"],
            warnings=validation_result["warnings"]
        )
    
    # ===== ANALYTICS =====
    
    async def get_aspects_analytics(self) -> EvaluationAspectAnalytics:
        """Get comprehensive aspects analytics."""
        analytics_data = await self.aspect_repo.get_aspects_analytics()
        
        # Get most/least used aspects
        aspects = await self.aspect_repo.get_active_aspects()
        most_used = []
        least_used = []
        avg_scores = {}
        
        for aspect in aspects[:10]:  # Limit to top 10
            stats = await self.aspect_repo.get_aspect_statistics(aspect.id)
            
            aspect_info = {
                "aspect_id": aspect.id,
                "aspect_name": aspect.aspect_name,
                "evaluation_count": stats["evaluation_count"],
                "avg_score": stats["avg_score"]
            }
            
            if stats["evaluation_count"] > 0:
                most_used.append(aspect_info)
                avg_scores[aspect.aspect_name] = stats["avg_score"]
            else:
                least_used.append(aspect_info)
        
        # Sort by usage
        most_used.sort(key=lambda x: x["evaluation_count"], reverse=True)
        least_used.sort(key=lambda x: x["evaluation_count"])
        
        return EvaluationAspectAnalytics(
            total_aspects=analytics_data["total_aspects"],
            active_aspects=analytics_data["active_aspects"],
            inactive_aspects=analytics_data["inactive_aspects"],
            total_weight=analytics_data["total_weight"],
            weight_distribution=analytics_data["weight_distribution"],
            most_used_aspects=most_used[:5],
            least_used_aspects=least_used[:5],
            avg_score_by_aspect=avg_scores
        )
    
    async def get_aspect_performance_analysis(self, aspect_id: int) -> AspectPerformanceAnalysis:
        """Get detailed performance analysis for an aspect."""
        aspect = await self.aspect_repo.get_by_id(aspect_id)
        if not aspect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation aspect not found"
            )
        
        analysis_data = await self.aspect_repo.get_aspect_performance_analysis(aspect_id)
        
        return AspectPerformanceAnalysis(
            aspect_id=aspect_id,
            aspect_name=aspect.aspect_name,
            total_evaluations=analysis_data["total_evaluations"],
            avg_score=analysis_data["avg_score"],
            min_score=analysis_data["min_score"],
            max_score=analysis_data["max_score"],
            score_distribution=analysis_data["score_distribution"],
            trend_data=[],  # Would need time-series data
            top_performers=analysis_data["top_performers"],
            improvement_needed=analysis_data["improvement_needed"]
        )
    
    async def get_comprehensive_stats(self) -> EvaluationAspectStats:
        """Get comprehensive evaluation aspect statistics."""
        # Get main analytics
        analytics = await self.get_aspects_analytics()
        
        # Get weight validation
        weight_validation = await self.validate_all_weights()
        
        # Get performance analysis for active aspects
        active_aspects = await self.aspect_repo.get_active_aspects()
        aspect_performance = []
        
        for aspect in active_aspects[:10]:  # Limit to prevent overload
            try:
                performance = await self.get_aspect_performance_analysis(aspect.id)
                aspect_performance.append(performance)
            except Exception:
                continue  # Skip aspects with issues
        
        # Generate recommendations
        recommendations = []
        if weight_validation.total_weight != 100:
            recommendations.append("Adjust aspect weights to total exactly 100%")
        
        if analytics.inactive_aspects > 0:
            recommendations.append(f"Review {analytics.inactive_aspects} inactive aspects")
        
        if len([a for a in analytics.most_used_aspects if a["evaluation_count"] == 0]) > 0:
            recommendations.append("Some aspects have never been used in evaluations")
        
        return EvaluationAspectStats(
            summary=analytics,
            aspect_performance=aspect_performance,
            weight_balance_check=weight_validation,
            usage_trends={},  # Would need historical data
            recommendations=recommendations
        )