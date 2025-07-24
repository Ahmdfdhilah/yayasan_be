"""Board member repository for CRUD operations."""

from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.board_member import BoardMember
from src.schemas.board_member import BoardMemberCreate, BoardMemberUpdate, BoardMemberFilterParams


class BoardMemberRepository:
    """Board member repository for CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, board_member_data: BoardMemberCreate, created_by: Optional[int] = None) -> BoardMember:
        """Create a new board member."""
        board_member = BoardMember(
            name=board_member_data.name,
            position=board_member_data.position,
            img_url=board_member_data.img_url,
            description=board_member_data.description,
            display_order=board_member_data.display_order,
            created_by=created_by
        )
        
        self.session.add(board_member)
        await self.session.commit()
        await self.session.refresh(board_member)
        return board_member
    
    async def get_by_id(self, board_member_id: int) -> Optional[BoardMember]:
        """Get board member by ID."""
        query = select(BoardMember).where(
            and_(BoardMember.id == board_member_id, BoardMember.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, board_member_id: int, board_member_data: BoardMemberUpdate, updated_by: Optional[int] = None) -> Optional[BoardMember]:
        """Update board member information."""
        board_member = await self.get_by_id(board_member_id)
        if not board_member:
            return None
        
        # Update fields
        update_data = board_member_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(board_member, key, value)
        
        board_member.updated_at = datetime.utcnow()
        board_member.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(board_member)
        return board_member
    
    async def soft_delete(self, board_member_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete board member."""
        query = (
            update(BoardMember)
            .where(BoardMember.id == board_member_id)
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def hard_delete(self, board_member_id: int) -> bool:
        """Permanently delete board member."""
        query = delete(BoardMember).where(BoardMember.id == board_member_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== FILTERING AND LISTING =====
    
    async def get_all_filtered(self, filters: BoardMemberFilterParams) -> Tuple[List[BoardMember], int]:
        """Get board members with filters and pagination."""
        # Base query
        query = select(BoardMember).where(BoardMember.deleted_at.is_(None))
        count_query = select(func.count(BoardMember.id)).where(BoardMember.deleted_at.is_(None))
        
        # Apply filters
        if filters.search:
            search_filter = or_(
                BoardMember.name.ilike(f"%{filters.search}%"),
                BoardMember.position.ilike(f"%{filters.search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        
        # Apply sorting
        if filters.sort_by == "name":
            sort_column = BoardMember.name
        elif filters.sort_by == "position":
            sort_column = BoardMember.position
        elif filters.sort_by == "created_at":
            sort_column = BoardMember.created_at
        elif filters.sort_by == "updated_at":
            sort_column = BoardMember.updated_at
        else:
            sort_column = BoardMember.display_order
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        board_members = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(board_members), total
    
    async def get_all_members(self, limit: Optional[int] = None) -> List[BoardMember]:
        """Get all board members."""
        query = select(BoardMember).where(
            BoardMember.deleted_at.is_(None)
        ).order_by(BoardMember.display_order.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_position(self, position: str) -> List[BoardMember]:
        """Get board members by position."""
        query = select(BoardMember).where(
            and_(
                BoardMember.deleted_at.is_(None),
                BoardMember.position.ilike(f"%{position}%")
            )
        ).order_by(BoardMember.display_order.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_display_order(self, board_member_id: int, new_order: int) -> bool:
        """Update display order for a board member."""
        query = (
            update(BoardMember)
            .where(BoardMember.id == board_member_id)
            .values(
                display_order=new_order,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_max_display_order(self) -> int:
        """Get the maximum display order."""
        query = select(func.max(BoardMember.display_order)).where(
            BoardMember.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        max_order = result.scalar()
        return max_order or 0
    
    async def count_all_members(self) -> int:
        """Count all board members."""
        query = select(func.count(BoardMember.id)).where(
            BoardMember.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def search_members(self, search_term: str, limit: Optional[int] = None) -> List[BoardMember]:
        """Search board members by name or position."""
        filters = [
            BoardMember.deleted_at.is_(None),
            or_(
                BoardMember.name.ilike(f"%{search_term}%"),
                BoardMember.position.ilike(f"%{search_term}%")
            )
        ]
        
        
        query = select(BoardMember).where(and_(*filters)).order_by(BoardMember.display_order.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())