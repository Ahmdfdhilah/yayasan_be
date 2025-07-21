"""MediaFile repository for unified schema system."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.media_file import MediaFile
from src.models.user import User
from src.models.organization import Organization
from src.schemas.media_file import MediaFileCreate, MediaFileUpdate
from src.schemas.media_file import MediaFileFilterParams


class MediaFileRepository:
    """MediaFile repository for unified schema system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== MEDIA FILE CRUD OPERATIONS =====
    
    async def create(self, file_data: MediaFileCreate) -> MediaFile:
        """Create media file record."""
        media_file = MediaFile(
            file_path=file_data.file_path,
            file_name=file_data.file_name,
            file_type=file_data.file_type,
            file_size=file_data.file_size,
            mime_type=file_data.mime_type,
            uploader_id=file_data.uploader_id,
            organization_id=file_data.organization_id,
            file_metadata=file_data.file_metadata,
            is_public=file_data.is_public
        )
        
        self.session.add(media_file)
        await self.session.commit()
        await self.session.refresh(media_file)
        return media_file
    
    async def get_by_id(self, file_id: int) -> Optional[MediaFile]:
        """Get media file by ID."""
        query = select(MediaFile).options(
            joinedload(MediaFile.uploader),
            joinedload(MediaFile.organization)
        ).where(
            and_(MediaFile.id == file_id, MediaFile.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_path(self, file_path: str) -> Optional[MediaFile]:
        """Get media file by path."""
        query = select(MediaFile).options(
            joinedload(MediaFile.uploader),
            joinedload(MediaFile.organization)
        ).where(
            and_(MediaFile.file_path == file_path, MediaFile.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, file_id: int, file_data: MediaFileUpdate) -> Optional[MediaFile]:
        """Update media file information."""
        media_file = await self.get_by_id(file_id)
        if not media_file:
            return None
        
        # Update fields
        update_data = file_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "file_metadata" and value:
                # Merge metadata instead of replacing
                if media_file.file_metadata:
                    media_file.file_metadata.update(value)
                else:
                    media_file.file_metadata = value
                continue
            setattr(media_file, key, value)
        
        media_file.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(media_file)
        return media_file
    
    async def soft_delete(self, file_id: int) -> bool:
        """Soft delete media file."""
        query = (
            update(MediaFile)
            .where(MediaFile.id == file_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def path_exists(self, file_path: str, exclude_file_id: Optional[int] = None) -> bool:
        """Check if file path already exists."""
        query = select(MediaFile).where(
            and_(
                MediaFile.file_path == file_path,
                MediaFile.deleted_at.is_(None)
            )
        )
        
        if exclude_file_id:
            query = query.where(MediaFile.id != exclude_file_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ===== MEDIA FILE FILTERING AND LISTING =====
    
    async def get_all_files_filtered(self, filters: MediaFileFilterParams) -> Tuple[List[MediaFile], int]:
        """Get media files with filters and pagination."""
        # Base query with relationships
        query = select(MediaFile).options(
            joinedload(MediaFile.uploader),
            joinedload(MediaFile.organization)
        ).where(MediaFile.deleted_at.is_(None))
        count_query = select(func.count(MediaFile.id)).where(MediaFile.deleted_at.is_(None))
        
        # Apply filters
        if filters.q:
            search_filter = or_(
                MediaFile.file_name.ilike(f"%{filters.q}%"),
                func.json_extract_path_text(MediaFile.file_metadata, 'description').ilike(f"%{filters.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.file_type:
            query = query.where(MediaFile.file_type == filters.file_type)
            count_query = count_query.where(MediaFile.file_type == filters.file_type)
        
        if filters.file_category:
            # This would need to be implemented based on file extension logic
            pass
        
        if filters.uploader_id:
            query = query.where(MediaFile.uploader_id == filters.uploader_id)
            count_query = count_query.where(MediaFile.uploader_id == filters.uploader_id)
        
        if filters.organization_id:
            query = query.where(MediaFile.organization_id == filters.organization_id)
            count_query = count_query.where(MediaFile.organization_id == filters.organization_id)
        
        if filters.is_public is not None:
            query = query.where(MediaFile.is_public == filters.is_public)
            count_query = count_query.where(MediaFile.is_public == filters.is_public)
        
        if filters.min_size:
            query = query.where(MediaFile.file_size >= filters.min_size)
            count_query = count_query.where(MediaFile.file_size >= filters.min_size)
        
        if filters.max_size:
            query = query.where(MediaFile.file_size <= filters.max_size)
            count_query = count_query.where(MediaFile.file_size <= filters.max_size)
        
        if filters.start_date:
            query = query.where(MediaFile.created_at >= filters.start_date)
            count_query = count_query.where(MediaFile.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.where(MediaFile.created_at <= filters.end_date)
            count_query = count_query.where(MediaFile.created_at <= filters.end_date)
        
        # Apply sorting
        if filters.sort_by == "file_name":
            sort_column = MediaFile.file_name
        elif filters.sort_by == "file_size":
            sort_column = MediaFile.file_size
        elif filters.sort_by == "file_type":
            sort_column = MediaFile.file_type
        elif filters.sort_by == "created_at":
            sort_column = MediaFile.created_at
        elif filters.sort_by == "updated_at":
            sort_column = MediaFile.updated_at
        else:
            sort_column = MediaFile.created_at
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)
        
        files = result.scalars().all()
        total_count = count_result.scalar()
        
        return list(files), total_count
    
    # ===== SPECIALIZED QUERIES =====
    
    async def get_by_uploader(self, uploader_id: int, limit: int = 10) -> List[MediaFile]:
        """Get files uploaded by specific user."""
        query = (
            select(MediaFile).options(
                joinedload(MediaFile.uploader),
                joinedload(MediaFile.organization)
            )
            .where(
                and_(
                    MediaFile.uploader_id == uploader_id,
                    MediaFile.deleted_at.is_(None)
                )
            )
            .order_by(MediaFile.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_organization(self, organization_id: int, limit: int = 10) -> List[MediaFile]:
        """Get files in specific organization."""
        query = (
            select(MediaFile).options(
                joinedload(MediaFile.uploader),
                joinedload(MediaFile.organization)
            )
            .where(
                and_(
                    MediaFile.organization_id == organization_id,
                    MediaFile.deleted_at.is_(None)
                )
            )
            .order_by(MediaFile.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_public_files(self, limit: int = 10) -> List[MediaFile]:
        """Get public files."""
        query = (
            select(MediaFile).options(
                joinedload(MediaFile.uploader),
                joinedload(MediaFile.organization)
            )
            .where(
                and_(
                    MediaFile.is_public == True,
                    MediaFile.deleted_at.is_(None)
                )
            )
            .order_by(MediaFile.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_file_type(self, file_type: str, limit: int = 10) -> List[MediaFile]:
        """Get files by type."""
        query = (
            select(MediaFile).options(
                joinedload(MediaFile.uploader),
                joinedload(MediaFile.organization)
            )
            .where(
                and_(
                    MediaFile.file_type == file_type,
                    MediaFile.deleted_at.is_(None)
                )
            )
            .order_by(MediaFile.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_files(self, search_term: str, limit: int = 10) -> List[MediaFile]:
        """Search files by name."""
        search_filter = MediaFile.file_name.ilike(f"%{search_term}%")
        
        query = (
            select(MediaFile).options(
                joinedload(MediaFile.uploader),
                joinedload(MediaFile.organization)
            )
            .where(
                and_(
                    search_filter,
                    MediaFile.deleted_at.is_(None)
                )
            )
            .order_by(MediaFile.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ===== METADATA MANAGEMENT =====
    
    async def update_metadata(self, file_id: int, metadata: Dict[str, Any]) -> bool:
        """Update file metadata."""
        media_file = await self.get_by_id(file_id)
        if not media_file:
            return False
        
        if media_file.file_metadata:
            media_file.file_metadata.update(metadata)
        else:
            media_file.file_metadata = metadata
        
        media_file.updated_at = datetime.utcnow()
        await self.session.commit()
        return True
    
    async def get_metadata(self, file_id: int, key: str) -> Optional[str]:
        """Get specific metadata field."""
        media_file = await self.get_by_id(file_id)
        if media_file:
            return media_file.get_metadata_field(key)
        return None
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_visibility(self, file_ids: List[int], is_public: bool) -> int:
        """Bulk update file visibility."""
        query = (
            update(MediaFile)
            .where(MediaFile.id.in_(file_ids))
            .values(
                is_public=is_public,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_move_to_organization(self, file_ids: List[int], organization_id: int) -> int:
        """Bulk move files to organization."""
        query = (
            update(MediaFile)
            .where(MediaFile.id.in_(file_ids))
            .values(
                organization_id=organization_id,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_soft_delete(self, file_ids: List[int]) -> int:
        """Bulk soft delete files."""
        query = (
            update(MediaFile)
            .where(MediaFile.id.in_(file_ids))
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== ANALYTICS =====
    
    async def get_storage_analytics(self) -> Dict[str, Any]:
        """Get file storage analytics."""
        # Total files and size
        total_query = select(
            func.count(MediaFile.id),
            func.sum(MediaFile.file_size)
        ).where(MediaFile.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_count, total_size = total_result.first()
        
        # Files by type
        type_stats_query = (
            select(MediaFile.file_type, func.count(MediaFile.id), func.sum(MediaFile.file_size))
            .where(MediaFile.deleted_at.is_(None))
            .group_by(MediaFile.file_type)
        )
        type_result = await self.session.execute(type_stats_query)
        type_stats = {row[0]: {"count": row[1], "size": row[2]} for row in type_result.all()}
        
        # Public vs private
        visibility_query = (
            select(MediaFile.is_public, func.count(MediaFile.id))
            .where(MediaFile.deleted_at.is_(None))
            .group_by(MediaFile.is_public)
        )
        visibility_result = await self.session.execute(visibility_query)
        visibility_stats = dict(visibility_result.all())
        
        return {
            "total_files": total_count or 0,
            "total_size_bytes": total_size or 0,
            "public_files": visibility_stats.get(True, 0),
            "private_files": visibility_stats.get(False, 0),
            "by_type": type_stats
        }