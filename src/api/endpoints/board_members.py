"""Board member management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.board_member import BoardMemberRepository
from src.services.board_member import BoardMemberService
from src.schemas.board_member import (
    BoardMemberCreate,
    BoardMemberUpdate,
    BoardMemberResponse,
    BoardMemberListResponse,
    BoardMemberSummary,
    BoardMemberFilterParams
)
from src.schemas.shared import MessageResponse
from src.auth.permissions import get_current_active_user, require_roles

router = APIRouter()

# Dependency for admin-only endpoints
admin_required = require_roles(["admin"])


async def get_board_member_service(session: AsyncSession = Depends(get_db)) -> BoardMemberService:
    """Get board member service dependency."""
    board_member_repo = BoardMemberRepository(session)
    return BoardMemberService(board_member_repo)


@router.post("/", response_model=BoardMemberResponse, summary="Create a new board member")
async def create_board_member(
    board_member_data: BoardMemberCreate,
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Create a new board member.
    
    Requires admin role.
    """
    return await board_member_service.create_board_member(board_member_data, current_user["id"])


@router.get("/", response_model=BoardMemberListResponse, summary="Get board members with filters")
async def get_board_members(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name or position"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Get board members with filters and pagination.
    
    Public endpoint - no authentication required.
    """
    filters = BoardMemberFilterParams(
        page=page,
        size=size,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await board_member_service.get_board_members(filters)


@router.get("/active", response_model=List[BoardMemberResponse], summary="Get active board members")
async def get_active_board_members(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Get active board members only.
    
    Public endpoint - no authentication required.
    """
    return await board_member_service.get_active_board_members(limit)


@router.get("/position/{position}", response_model=List[BoardMemberResponse], summary="Get board members by position")
async def get_board_members_by_position(
    position: str,
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Get board members by position.
    
    Public endpoint - no authentication required.
    """
    return await board_member_service.get_board_members_by_position(position)


@router.get("/search", response_model=List[BoardMemberResponse], summary="Search board members")
async def search_board_members(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    active_only: bool = Query(True, description="Only return active members"),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Search board members by name or position.
    
    Public endpoint - no authentication required.
    """
    return await board_member_service.search_board_members(q, active_only, limit)


@router.get("/statistics", summary="Get board member statistics")
async def get_board_member_statistics(
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Get board member statistics.
    
    Requires admin role.
    """
    return await board_member_service.get_board_member_statistics()


@router.get("/summaries", response_model=List[BoardMemberSummary], summary="Get board member summaries")
async def get_board_member_summaries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Get board member summaries (lighter response).
    
    Public endpoint - no authentication required.
    """
    filters = BoardMemberFilterParams(
        page=page,
        size=size,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await board_member_service.get_board_member_summaries(filters)


@router.get("/{board_member_id}", response_model=BoardMemberResponse, summary="Get board member by ID")
async def get_board_member(
    board_member_id: int,
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Get board member by ID.
    
    Public endpoint - no authentication required.
    """
    return await board_member_service.get_board_member(board_member_id)


@router.put("/{board_member_id}", response_model=BoardMemberResponse, summary="Update board member")
async def update_board_member(
    board_member_id: int,
    board_member_data: BoardMemberUpdate,
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Update board member.
    
    Requires admin role.
    """
    return await board_member_service.update_board_member(board_member_id, board_member_data, current_user["id"])


@router.delete("/{board_member_id}", response_model=MessageResponse, summary="Delete board member")
async def delete_board_member(
    board_member_id: int,
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Delete board member (soft delete).
    
    Requires admin role.
    """
    return await board_member_service.delete_board_member(board_member_id, current_user["id"])


@router.patch("/{board_member_id}/display-order", response_model=BoardMemberResponse, summary="Update board member display order")
async def update_display_order(
    board_member_id: int,
    new_order: int = Body(..., ge=0, description="New display order"),
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Update display order for a board member.
    
    Requires admin role.
    """
    return await board_member_service.update_display_order(board_member_id, new_order)


@router.patch("/{board_member_id}/toggle-active", response_model=BoardMemberResponse, summary="Toggle board member active status")
async def toggle_active_status(
    board_member_id: int,
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    """
    Toggle active status of a board member.
    
    Requires admin role.
    """
    return await board_member_service.toggle_active_status(board_member_id, current_user["id"])