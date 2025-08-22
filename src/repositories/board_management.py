"""Board management repositories for database operations."""

from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update
from sqlalchemy.orm import selectinload

from src.models.board_group import BoardGroup
from src.models.board_member import BoardMember
from src.schemas.board_management import BoardGroupFilterParams, BoardMemberFilterParams


class BoardGroupRepository:
    """Repository for board group operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, board_group_data: dict) -> BoardGroup:
        """Create a new board group."""
        display_order = board_group_data.get("display_order")

        if display_order:
            # Shift existing groups with same or higher display_order
            await self._shift_display_orders(display_order, shift_up=True)

        board_group = BoardGroup(**board_group_data)
        self.session.add(board_group)
        await self.session.commit()
        await self.session.refresh(board_group)
        return board_group

    async def get_by_id(self, board_group_id: int) -> Optional[BoardGroup]:
        """Get board group by ID."""
        query = select(BoardGroup).where(BoardGroup.id == board_group_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, board_group_id: int, update_data: dict) -> BoardGroup:
        """Update board group."""
        new_display_order = update_data.get("display_order")

        if new_display_order:
            # Get current display_order
            current_group = await self.get_by_id(board_group_id)
            current_display_order = (
                current_group.display_order if current_group else None
            )

            if current_display_order != new_display_order:
                # Shift existing groups
                await self._shift_display_orders(
                    new_display_order, shift_up=True, exclude_id=board_group_id
                )

        stmt = (
            update(BoardGroup)
            .where(BoardGroup.id == board_group_id)
            .values(**update_data)
            .returning(BoardGroup)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def delete(self, board_group_id: int) -> None:
        """Delete board group."""
        # Check if there are board members referencing this group
        member_count_query = select(func.count(BoardMember.id)).where(
            BoardMember.group_id == board_group_id
        )
        member_count_result = await self.session.execute(member_count_query)
        member_count = member_count_result.scalar() or 0

        if member_count > 0:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tidak dapat menghapus grup board. Masih ada {member_count} anggota board yang terikat pada grup ini. Silakan pindahkan atau hapus anggota terlebih dahulu.",
            )

        stmt = delete(BoardGroup).where(BoardGroup.id == board_group_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_all_filtered(
        self, filters: BoardGroupFilterParams
    ) -> Tuple[List[BoardGroup], int]:
        """Get board groups with filters and pagination."""
        query = select(BoardGroup).options(selectinload(BoardGroup.members))
        count_query = select(func.count(BoardGroup.id))

        # Apply search filter
        if filters.search:
            search_filter = or_(
                BoardGroup.title.ilike(f"%{filters.search}%"),
                BoardGroup.description.ilike(f"%{filters.search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if filters.sort_by == "title":
            sort_column = BoardGroup.title
        elif filters.sort_by == "created_at":
            sort_column = BoardGroup.created_at
        elif filters.sort_by == "updated_at":
            sort_column = BoardGroup.updated_at
        else:
            sort_column = BoardGroup.display_order

        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)

        # Execute query
        result = await self.session.execute(query)
        board_groups = result.scalars().all()

        return list(board_groups), total

    async def get_by_id_with_members(self, board_group_id: int) -> Optional[BoardGroup]:
        """Get board group by ID with members."""
        query = (
            select(BoardGroup)
            .options(selectinload(BoardGroup.members))
            .where(BoardGroup.id == board_group_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_ordered(self) -> List[BoardGroup]:
        """Get all board groups ordered by display_order."""
        query = (
            select(BoardGroup)
            .options(selectinload(BoardGroup.members))
            .order_by(BoardGroup.display_order.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _shift_display_orders(
        self, from_order: int, shift_up: bool = True, exclude_id: Optional[int] = None
    ) -> None:
        """Shift display orders to make room for new/updated group."""
        conditions = [BoardGroup.display_order >= from_order]
        if exclude_id:
            conditions.append(BoardGroup.id != exclude_id)

        # Shift all groups at or after the target position
        if shift_up:
            stmt = (
                update(BoardGroup)
                .where(*conditions)
                .values(display_order=BoardGroup.display_order + 1)
            )
        else:
            stmt = (
                update(BoardGroup)
                .where(*conditions)
                .values(display_order=BoardGroup.display_order - 1)
            )

        await self.session.execute(stmt)
        await self.session.flush()  # Don't commit yet, let the main operation handle it


class BoardMemberRepository:
    """Repository for board member operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, board_member_data: dict) -> BoardMember:
        """Create a new board member."""
        group_id = board_member_data.get("group_id")
        member_order = board_member_data.get("member_order", 1)

        if group_id and member_order:
            # Shift existing members in the same group
            await self._shift_member_orders(group_id, member_order, shift_up=True)

        board_member = BoardMember(**board_member_data)
        self.session.add(board_member)
        await self.session.commit()
        await self.session.refresh(board_member)
        return board_member

    async def get_by_id(self, board_member_id: int) -> Optional[BoardMember]:
        """Get board member by ID."""
        query = select(BoardMember).where(BoardMember.id == board_member_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, board_member_id: int, update_data: dict) -> BoardMember:
        """Update board member."""
        new_group_id = update_data.get("group_id")
        new_member_order = update_data.get("member_order")

        if new_group_id and new_member_order:
            # Get current member info
            current_member = await self.get_by_id(board_member_id)
            current_group_id = current_member.group_id if current_member else None
            current_member_order = (
                current_member.member_order if current_member else None
            )

            # If group or order changed, handle shifting
            if (current_group_id != new_group_id) or (
                current_member_order != new_member_order
            ):
                await self._shift_member_orders(
                    new_group_id,
                    new_member_order,
                    shift_up=True,
                    exclude_id=board_member_id,
                )

        stmt = (
            update(BoardMember)
            .where(BoardMember.id == board_member_id)
            .values(**update_data)
            .returning(BoardMember)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def delete(self, board_member_id: int) -> None:
        """Delete board member."""
        stmt = delete(BoardMember).where(BoardMember.id == board_member_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_all_filtered(
        self, filters: BoardMemberFilterParams
    ) -> Tuple[List[BoardMember], int]:
        """Get board members with filters and pagination."""
        query = select(BoardMember).options(selectinload(BoardMember.group))
        count_query = select(func.count(BoardMember.id))

        # Apply search filter
        if filters.search:
            search_filter = or_(
                BoardMember.name.ilike(f"%{filters.search}%"),
                BoardMember.position.ilike(f"%{filters.search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

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
            sort_column = BoardMember.member_order

        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)

        # Execute query
        result = await self.session.execute(query)
        board_members = result.scalars().all()

        return list(board_members), total

    async def get_by_group_id(self, group_id: int) -> List[BoardMember]:
        """Get board members by group ID ordered by member_order."""
        query = (
            select(BoardMember)
            .where(BoardMember.group_id == group_id)
            .order_by(BoardMember.member_order.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _shift_member_orders(
        self,
        group_id: int,
        from_order: int,
        shift_up: bool = True,
        exclude_id: Optional[int] = None,
    ) -> None:
        """Shift member orders within a group to make room for new/updated member."""
        conditions = [
            BoardMember.group_id == group_id,
            BoardMember.member_order >= from_order,
        ]
        if exclude_id:
            conditions.append(BoardMember.id != exclude_id)

        # Shift all members in the same group at or after the target position
        if shift_up:
            stmt = (
                update(BoardMember)
                .where(*conditions)
                .values(member_order=BoardMember.member_order + 1)
            )
        else:
            stmt = (
                update(BoardMember)
                .where(*conditions)
                .values(member_order=BoardMember.member_order - 1)
            )

        await self.session.execute(stmt)
        await self.session.flush()  # Don't commit yet, let the main operation handle it
