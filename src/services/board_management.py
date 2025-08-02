"""Board management business logic services."""

from typing import List
from fastapi import HTTPException, status

from src.repositories.board_management import BoardGroupRepository, BoardMemberRepository
from src.schemas.board_management import (
    BoardGroupCreate,
    BoardGroupUpdate,
    BoardGroupResponse,
    BoardGroupListResponse,
    BoardGroupFilterParams,
    BoardMemberCreate,
    BoardMemberUpdate,
    BoardMemberResponse,
    BoardMemberListResponse,
    BoardMemberFilterParams
)
from src.schemas.shared import MessageResponse


class BoardGroupService:
    """Service for board group business logic."""

    def __init__(self, board_group_repo: BoardGroupRepository):
        self.board_group_repo = board_group_repo

    def _calculate_pages(self, total: int, size: int) -> int:
        """Calculate total pages."""
        return (total + size - 1) // size

    async def create_board_group(
        self, 
        board_group_data: BoardGroupCreate, 
        user_id: int
    ) -> BoardGroupResponse:
        """Create a new board group."""
        board_group = await self.board_group_repo.create(board_group_data.model_dump())
        return BoardGroupResponse.model_validate(board_group)

    async def get_board_groups(
        self, 
        filters: BoardGroupFilterParams
    ) -> BoardGroupListResponse:
        """Get board groups with filters and pagination."""
        board_groups, total = await self.board_group_repo.get_all_filtered(filters)
        
        return BoardGroupListResponse(
            items=[BoardGroupResponse.model_validate(bg) for bg in board_groups],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=self._calculate_pages(total, filters.size)
        )

    async def get_board_group(self, board_group_id: int) -> BoardGroupResponse:
        """Get board group by ID."""
        board_group = await self.board_group_repo.get_by_id(board_group_id)
        if not board_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board group not found"
            )
        return BoardGroupResponse.model_validate(board_group)

    async def update_board_group(
        self, 
        board_group_id: int, 
        board_group_data: BoardGroupUpdate, 
        user_id: int
    ) -> BoardGroupResponse:
        """Update board group."""
        board_group = await self.board_group_repo.get_by_id(board_group_id)
        if not board_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board group not found"
            )

        # Filter out None values
        update_data = {k: v for k, v in board_group_data.model_dump().items() if v is not None}
        
        updated_board_group = await self.board_group_repo.update(board_group_id, update_data)
        return BoardGroupResponse.model_validate(updated_board_group)

    async def delete_board_group(self, board_group_id: int, user_id: int) -> MessageResponse:
        """Delete board group."""
        board_group = await self.board_group_repo.get_by_id(board_group_id)
        if not board_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board group not found"
            )

        await self.board_group_repo.delete(board_group_id)
        return MessageResponse(message="Board group deleted successfully")


class BoardMemberService:
    """Service for board member business logic."""

    def __init__(self, board_member_repo: BoardMemberRepository):
        self.board_member_repo = board_member_repo

    def _calculate_pages(self, total: int, size: int) -> int:
        """Calculate total pages."""
        return (total + size - 1) // size

    async def create_board_member(
        self, 
        board_member_data: BoardMemberCreate, 
        user_id: int
    ) -> BoardMemberResponse:
        """Create a new board member."""
        board_member = await self.board_member_repo.create(board_member_data.model_dump())
        return BoardMemberResponse.model_validate(board_member)

    async def get_board_members(
        self, 
        filters: BoardMemberFilterParams
    ) -> BoardMemberListResponse:
        """Get board members with filters and pagination."""
        board_members, total = await self.board_member_repo.get_all_filtered(filters)
        
        return BoardMemberListResponse(
            items=[BoardMemberResponse.model_validate(bm) for bm in board_members],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=self._calculate_pages(total, filters.size)
        )

    async def get_board_member(self, board_member_id: int) -> BoardMemberResponse:
        """Get board member by ID."""
        board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )
        return BoardMemberResponse.model_validate(board_member)

    async def update_board_member(
        self, 
        board_member_id: int, 
        board_member_data: BoardMemberUpdate, 
        user_id: int
    ) -> BoardMemberResponse:
        """Update board member."""
        board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )

        # Filter out None values
        update_data = {k: v for k, v in board_member_data.model_dump().items() if v is not None}
        
        updated_board_member = await self.board_member_repo.update(board_member_id, update_data)
        return BoardMemberResponse.model_validate(updated_board_member)

    async def delete_board_member(self, board_member_id: int, user_id: int) -> MessageResponse:
        """Delete board member."""
        board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )

        await self.board_member_repo.delete(board_member_id)
        return MessageResponse(message="Board member deleted successfully")