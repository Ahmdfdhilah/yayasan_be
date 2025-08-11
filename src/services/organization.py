"""Organization service for unified schema system."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.organization import OrganizationRepository
from src.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, 
    OrganizationListResponse, OrganizationSummary, AssignHeadRequest, RemoveHeadRequest
)
from src.schemas.shared import MessageResponse
from src.schemas.organization import OrganizationFilterParams
from src.models.organization import Organization
from src.utils.messages import get_message
# Remove OrganizationType import as it's no longer used


class OrganizationService:
    """Organization service for unified schema system."""
    
    def __init__(self, org_repo: OrganizationRepository):
        self.org_repo = org_repo
    
    async def create_organization(self, org_data: OrganizationCreate) -> OrganizationResponse:
        """Create organization."""
        # Validate name uniqueness
        if await self.org_repo.name_exists(org_data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_message("organization", "name_exists")
            )
        
        # Validate head_id if provided
        if org_data.head_id:
            head_user = await self.org_repo.get_user_by_id(org_data.head_id)
            if not head_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=get_message("user", "not_found")
                )
        
        # Create organization in database
        organization = await self.org_repo.create(org_data)
        
        # Get user count and head name
        user_count = await self.org_repo.get_user_count(organization.id)
        head_name = None
        if organization.head_id:
            head_user = await self.org_repo.get_user_by_id(organization.head_id)
            head_name = head_user.display_name if head_user else None
        
        # Convert to response
        return OrganizationResponse.from_organization_model(organization, user_count, head_name)
    
    async def get_organization(self, org_id: int) -> OrganizationResponse:
        """Get organization by ID."""
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("organization", "not_found")
            )
        
        # Get user count and head name
        user_count = await self.org_repo.get_user_count(org_id)
        head_name = None
        if organization.head_id:
            head_user = await self.org_repo.get_user_by_id(organization.head_id)
            head_name = head_user.display_name if head_user else None
        
        return OrganizationResponse.from_organization_model(organization, user_count, head_name)
    
    
    async def update_organization(self, org_id: int, org_data: OrganizationUpdate) -> OrganizationResponse:
        """Update organization information."""
        # Check if organization exists
        existing_org = await self.org_repo.get_by_id(org_id)
        if not existing_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("organization", "not_found")
            )
        
        # Validate name uniqueness if being updated
        if org_data.name and await self.org_repo.name_exists(org_data.name, exclude_org_id=org_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists"
            )
        
        # Validate head_id if being updated
        if org_data.head_id:
            head_user = await self.org_repo.get_user_by_id(org_data.head_id)
            if not head_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=get_message("user", "not_found")
                )
            # Ensure head user belongs to this organization
            if head_user.organization_id != org_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Head user must belong to this organization"
                )
        
        # Update organization in database
        updated_org = await self.org_repo.update(org_id, org_data)
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update organization"
            )
        
        # Get user count and head name
        user_count = await self.org_repo.get_user_count(org_id)
        head_name = None
        if updated_org.head_id:
            head_user = await self.org_repo.get_user_by_id(updated_org.head_id)
            head_name = head_user.display_name if head_user else None
        
        return OrganizationResponse.from_organization_model(updated_org, user_count, head_name)
    
    async def delete_organization(self, org_id: int) -> MessageResponse:
        """Delete organization (soft delete)."""
        # Check if organization exists
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("organization", "not_found")
            )
        
        # Check if organization has users
        user_count = await self.org_repo.get_user_count(org_id)
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete organization with {user_count} users. Please reassign users first."
            )
        
        # Soft delete organization
        success = await self.org_repo.soft_delete(org_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete organization"
            )
        
        return MessageResponse(message="Organization deleted successfully")
    
    async def get_organizations(self, filters: OrganizationFilterParams) -> OrganizationListResponse:
        """Get organizations with filters and pagination."""
        organizations, total_count = await self.org_repo.get_all_organizations_filtered(filters)
        
        # Get user counts for all organizations
        org_ids = [org.id for org in organizations]
        user_counts = await self.org_repo.get_organizations_with_user_counts(org_ids)
        
        # Convert to response objects
        org_responses = []
        for org in organizations:
            user_count = user_counts.get(org.id, 0)
            head_name = None
            if org.head_id:
                head_user = await self.org_repo.get_user_by_id(org.head_id)
                head_name = head_user.display_name if head_user else None
            
            org_responses.append(
                OrganizationResponse.from_organization_model(org, user_count, head_name)
            )
        
        # Calculate pagination metadata
        total_pages = (total_count + filters.size - 1) // filters.size
        
        return OrganizationListResponse(
            items=org_responses,
            total=total_count,
            page=filters.page,
            size=filters.size,
            pages=total_pages
        )
    
    
    async def search_organizations(self, search_term: str, limit: int = 10) -> List[OrganizationSummary]:
        """Search organizations."""
        organizations = await self.org_repo.search_organizations(search_term, limit)
        
        # Get user counts
        org_ids = [org.id for org in organizations]
        user_counts = await self.org_repo.get_organizations_with_user_counts(org_ids)
        
        return [
            OrganizationSummary.from_organization_model(
                org, 
                user_counts.get(org.id, 0)
            ) 
            for org in organizations
        ]
    
    async def get_recent_organizations(self, limit: int = 10) -> List[OrganizationSummary]:
        """Get recently created organizations."""
        organizations = await self.org_repo.get_recent_organizations(limit)
        
        # Get user counts
        org_ids = [org.id for org in organizations]
        user_counts = await self.org_repo.get_organizations_with_user_counts(org_ids)
        
        return [
            OrganizationSummary.from_organization_model(
                org, 
                user_counts.get(org.id, 0)
            ) 
            for org in organizations
        ]
    
    # ===== HEAD MANAGEMENT =====
    
    async def assign_head(self, org_id: int, assign_data: AssignHeadRequest) -> OrganizationResponse:
        """Assign a head to an organization."""
        # Check if organization exists
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("organization", "not_found")
            )
        
        # Validate user exists
        head_user = await self.org_repo.get_user_by_id(assign_data.user_id)
        if not head_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Ensure user belongs to this organization
        if head_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to this organization"
            )
        
        # Check if user has kepala_sekolah role
        if not head_user.is_kepala_sekolah():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must have 'kepala_sekolah' role to be assigned as head"
            )
        
        # Update organization head
        update_data = OrganizationUpdate(head_id=assign_data.user_id)
        updated_org = await self.org_repo.update(org_id, update_data)
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign head"
            )
        
        # Return updated organization
        return await self.get_organization(org_id)
    
    async def remove_head(self, org_id: int, remove_data: RemoveHeadRequest) -> OrganizationResponse:
        """Remove head from an organization."""
        if not remove_data.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required to remove head"
            )
        
        # Check if organization exists
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("organization", "not_found")
            )
        
        if not organization.head_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization has no head assigned"
            )
        
        # Remove head
        update_data = OrganizationUpdate(head_id=None)
        updated_org = await self.org_repo.update(org_id, update_data)
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove head"
            )
        
        # Return updated organization
        return await self.get_organization(org_id)
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_delete_organizations(self, org_ids: List[int], force: bool = False) -> MessageResponse:
        """Bulk delete organizations."""
        # Check if organizations have users (unless force delete)
        if not force:
            user_counts = await self.org_repo.get_organizations_with_user_counts(org_ids)
            orgs_with_users = [org_id for org_id, count in user_counts.items() if count > 0]
            
            if orgs_with_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Organizations {orgs_with_users} have users. Use force=true to delete anyway."
                )
        
        # Perform bulk delete
        deleted_count = await self.org_repo.bulk_soft_delete(org_ids)
        
        return MessageResponse(
            message=f"Successfully deleted {deleted_count} organizations"
        )
    
    # ===== ANALYTICS =====
    
    async def get_organization_analytics(self) -> Dict[str, Any]:
        """Get organization statistics and analytics."""
        stats = await self.org_repo.get_organization_stats()
        
        # Add additional computed metrics
        total_orgs = stats["total_organizations"]
        utilization_rate = (stats["organizations_with_users"] / total_orgs * 100) if total_orgs > 0 else 0
        
        stats["utilization_rate"] = round(utilization_rate, 2)
        
        return stats
    
    # ===== VALIDATION HELPERS =====
    
    async def validate_organization_exists(self, org_id: int) -> Organization:
        """Validate organization exists and return it."""
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("organization", "not_found")
            )
        return organization
    
    async def validate_organization_name_available(self, name: str, exclude_org_id: Optional[int] = None) -> bool:
        """Validate organization name is available."""
        exists = await self.org_repo.name_exists(name, exclude_org_id)
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists"
            )
        return True
    
