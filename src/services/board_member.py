"""Board member service for business logic."""

from typing import Optional, List
from fastapi import HTTPException, status

from src.repositories.board_member import BoardMemberRepository
from src.schemas.board_member import (
    BoardMemberCreate, BoardMemberUpdate, BoardMemberResponse, BoardMemberListResponse,
    BoardMemberSummary, BoardMemberFilterParams
)
from src.schemas.shared import MessageResponse


class BoardMemberService:
    """Board member service for business logic."""
    
    def __init__(self, board_member_repo: BoardMemberRepository):
        self.board_member_repo = board_member_repo
    
    async def create_board_member(self, board_member_data: BoardMemberCreate, created_by: Optional[int] = None) -> BoardMemberResponse:
        """Create a new board member."""
        # If no display_order specified, set to next available
        if board_member_data.display_order == 0:
            max_order = await self.board_member_repo.get_max_display_order()
            board_member_data.display_order = max_order + 1
        
        # Create board member in database
        board_member = await self.board_member_repo.create(board_member_data, created_by)
        
        return BoardMemberResponse.from_board_member_model(board_member)
    
    async def get_board_member(self, board_member_id: int) -> BoardMemberResponse:
        """Get board member by ID."""
        board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )
        
        return BoardMemberResponse.from_board_member_model(board_member)
    
    async def update_board_member(self, board_member_id: int, board_member_data: BoardMemberUpdate, updated_by: Optional[int] = None) -> BoardMemberResponse:
        """Update board member information."""
        # Check if board member exists
        existing_board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not existing_board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )
        
        # Update board member in database
        updated_board_member = await self.board_member_repo.update(board_member_id, board_member_data, updated_by)
        if not updated_board_member:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update board member"
            )
        
        return BoardMemberResponse.from_board_member_model(updated_board_member)
    
    async def delete_board_member(self, board_member_id: int, deleted_by: Optional[int] = None) -> MessageResponse:
        """Delete board member (soft delete)."""
        # Check if board member exists
        existing_board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not existing_board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )
        
        # Soft delete board member
        success = await self.board_member_repo.soft_delete(board_member_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete board member"
            )
        
        return MessageResponse(message="Board member deleted successfully")
    
    async def get_board_members(self, filters: BoardMemberFilterParams) -> BoardMemberListResponse:
        """Get board members with filters and pagination."""
        board_members, total = await self.board_member_repo.get_all_filtered(filters)
        
        board_member_responses = [BoardMemberResponse.from_board_member_model(board_member) for board_member in board_members]
        
        return BoardMemberListResponse(
            items=board_member_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    async def get_active_board_members(self, limit: Optional[int] = None) -> List[BoardMemberResponse]:
        """Get active board members only."""
        board_members = await self.board_member_repo.get_active_members(limit)
        return [BoardMemberResponse.from_board_member_model(board_member) for board_member in board_members]
    
    async def get_board_members_by_position(self, position: str) -> List[BoardMemberResponse]:
        """Get board members by position."""
        board_members = await self.board_member_repo.get_by_position(position)
        return [BoardMemberResponse.from_board_member_model(board_member) for board_member in board_members]
    
    async def update_display_order(self, board_member_id: int, new_order: int) -> BoardMemberResponse:
        """Update display order for a board member."""
        # Check if board member exists
        existing_board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not existing_board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )
        
        # Update display order
        success = await self.board_member_repo.update_display_order(board_member_id, new_order)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update display order"
            )
        
        # Return updated board member
        updated_board_member = await self.board_member_repo.get_by_id(board_member_id)
        return BoardMemberResponse.from_board_member_model(updated_board_member)
    
    async def search_board_members(self, search_term: str, active_only: bool = True, limit: Optional[int] = None) -> List[BoardMemberResponse]:
        """Search board members by name or position."""
        board_members = await self.board_member_repo.search_members(search_term, active_only, limit)
        return [BoardMemberResponse.from_board_member_model(board_member) for board_member in board_members]
    
    async def get_board_member_summaries(self, filters: BoardMemberFilterParams) -> List[BoardMemberSummary]:
        """Get board member summaries (lighter response)."""
        board_members, _ = await self.board_member_repo.get_all_filtered(filters)
        return [BoardMemberSummary.from_board_member_model(board_member) for board_member in board_members]
    
    async def toggle_active_status(self, board_member_id: int, updated_by: Optional[int] = None) -> BoardMemberResponse:
        """Toggle active status of a board member."""
        # Check if board member exists
        existing_board_member = await self.board_member_repo.get_by_id(board_member_id)
        if not existing_board_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board member not found"
            )
        
        # Toggle active status
        update_data = BoardMemberUpdate(is_active=not existing_board_member.is_active)
        updated_board_member = await self.board_member_repo.update(board_member_id, update_data, updated_by)
        
        if not updated_board_member:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to toggle active status"
            )
        
        return BoardMemberResponse.from_board_member_model(updated_board_member)
    
    async def get_board_member_statistics(self) -> dict:
        """Get board member statistics."""
        total_members = len(await self.board_member_repo.get_all_filtered(BoardMemberFilterParams())[0])
        active_members = await self.board_member_repo.count_active_members()
        inactive_members = total_members - active_members
        
        return {
            "total_members": total_members,
            "active_members": active_members,
            "inactive_members": inactive_members
        }