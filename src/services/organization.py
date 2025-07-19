"""Organization service for unified schema system."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.organization import OrganizationRepository
from src.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, 
    OrganizationListResponse, OrganizationSummary, ContactInfoUpdate, SettingsUpdate
)
from src.schemas.shared import MessageResponse
from src.schemas.filters import OrganizationFilterParams
from src.models.organization import Organization
from src.models.enums import OrganizationType


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
                detail="Organization name already exists"
            )
        
        # Validate slug uniqueness if provided
        if org_data.slug and await self.org_repo.slug_exists(org_data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already exists"
            )
        
        # Create organization in database
        organization = await self.org_repo.create(org_data)
        
        # Get user count
        user_count = await self.org_repo.get_user_count(organization.id)
        
        # Convert to response
        return OrganizationResponse.from_organization_model(organization, user_count)
    
    async def get_organization(self, org_id: int) -> OrganizationResponse:
        """Get organization by ID."""
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user count
        user_count = await self.org_repo.get_user_count(org_id)
        
        return OrganizationResponse.from_organization_model(organization, user_count)
    
    async def get_organization_by_slug(self, slug: str) -> OrganizationResponse:
        """Get organization by slug."""
        organization = await self.org_repo.get_by_slug(slug)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get user count
        user_count = await self.org_repo.get_user_count(organization.id)
        
        return OrganizationResponse.from_organization_model(organization, user_count)
    
    async def update_organization(self, org_id: int, org_data: OrganizationUpdate) -> OrganizationResponse:
        """Update organization information."""
        # Check if organization exists
        existing_org = await self.org_repo.get_by_id(org_id)
        if not existing_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate name uniqueness if being updated
        if org_data.name and await self.org_repo.name_exists(org_data.name, exclude_org_id=org_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists"
            )
        
        # Validate slug uniqueness if being updated
        if org_data.slug and await self.org_repo.slug_exists(org_data.slug, exclude_org_id=org_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already exists"
            )
        
        # Update organization in database
        updated_org = await self.org_repo.update(org_id, org_data)
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update organization"
            )
        
        # Get user count
        user_count = await self.org_repo.get_user_count(org_id)
        
        return OrganizationResponse.from_organization_model(updated_org, user_count)
    
    async def delete_organization(self, org_id: int) -> MessageResponse:
        """Delete organization (soft delete)."""
        # Check if organization exists
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
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
        org_responses = [
            OrganizationResponse.from_organization_model(
                org, 
                user_counts.get(org.id, 0)
            ) 
            for org in organizations
        ]
        
        # Calculate pagination metadata
        total_pages = (total_count + filters.size - 1) // filters.size
        
        return OrganizationListResponse(
            items=org_responses,
            total=total_count,
            page=filters.page,
            size=filters.size,
            pages=total_pages
        )
    
    async def get_organizations_by_type(self, org_type: OrganizationType) -> List[OrganizationSummary]:
        """Get organizations by type."""
        organizations = await self.org_repo.get_by_type(org_type)
        
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
    
    # ===== CONTACT INFO MANAGEMENT =====
    
    async def update_contact_info(self, org_id: int, contact_data: ContactInfoUpdate) -> OrganizationResponse:
        """Update organization contact information."""
        # Check if organization exists
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Convert to dict and filter out None values
        contact_dict = {k: v for k, v in contact_data.model_dump().items() if v is not None}
        
        # Update contact info
        success = await self.org_repo.update_contact_info(org_id, contact_dict)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update contact information"
            )
        
        # Return updated organization
        return await self.get_organization(org_id)
    
    async def update_settings(self, org_id: int, settings_data: SettingsUpdate) -> OrganizationResponse:
        """Update organization settings."""
        # Check if organization exists
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Convert to dict and filter out None values
        settings_dict = {k: v for k, v in settings_data.model_dump().items() if v is not None}
        
        # Update settings
        success = await self.org_repo.update_settings(org_id, settings_dict)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update settings"
            )
        
        # Return updated organization
        return await self.get_organization(org_id)
    
    async def get_contact_info(self, org_id: int, key: str) -> str:
        """Get specific contact information."""
        value = await self.org_repo.get_contact_info(org_id, key)
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact info '{key}' not found"
            )
        return value
    
    async def get_setting(self, org_id: int, key: str) -> str:
        """Get specific organization setting."""
        value = await self.org_repo.get_setting(org_id, key)
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        return value
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_type(self, org_ids: List[int], new_type: OrganizationType) -> MessageResponse:
        """Bulk update organization type."""
        # Validate all organizations exist
        for org_id in org_ids:
            organization = await self.org_repo.get_by_id(org_id)
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Organization {org_id} not found"
                )
        
        # Perform bulk update
        updated_count = await self.org_repo.bulk_update_type(org_ids, new_type)
        
        return MessageResponse(
            message=f"Successfully updated {updated_count} organizations to type {new_type.value}"
        )
    
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
                detail="Organization not found"
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
    
    async def validate_organization_slug_available(self, slug: str, exclude_org_id: Optional[int] = None) -> bool:
        """Validate organization slug is available."""
        exists = await self.org_repo.slug_exists(slug, exclude_org_id)
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already exists"
            )
        return True