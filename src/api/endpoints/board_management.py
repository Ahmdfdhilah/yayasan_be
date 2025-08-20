"""Board management endpoints - Groups and Members."""

from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.board_management import BoardGroupRepository, BoardMemberRepository
from src.services.board_management import BoardGroupService, BoardMemberService
from src.schemas.board_management import (
    BoardGroupCreate,
    BoardGroupUpdate,
    BoardGroupFilterParams,
    BoardMemberCreate,
    BoardMemberUpdate,
    BoardMemberFilterParams
)
from src.auth.permissions import admin_required
from src.utils.direct_file_upload import (
    DirectFileUploader,
    get_board_member_multipart,
    get_board_member_multipart_update,
    process_image_upload,
    merge_data_with_image_url
)

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_board_group_service(session: AsyncSession = Depends(get_db)) -> BoardGroupService:
    """Get board group service dependency."""
    board_group_repo = BoardGroupRepository(session)
    return BoardGroupService(board_group_repo)


async def get_board_member_service(session: AsyncSession = Depends(get_db)) -> BoardMemberService:
    """Get board member service dependency."""
    board_member_repo = BoardMemberRepository(session)
    return BoardMemberService(board_member_repo)


# ===== BOARD GROUP ENDPOINTS =====

@router.post("/groups")
async def create_board_group(
    board_group_data: BoardGroupCreate,
    current_user: dict = Depends(admin_required),
    board_group_service: BoardGroupService = Depends(get_board_group_service),
):
    return await board_group_service.create_board_group(board_group_data, current_user["id"])


@router.get("/groups")
async def get_board_groups(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    board_group_service: BoardGroupService = Depends(get_board_group_service),
):
    filters = BoardGroupFilterParams(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await board_group_service.get_board_groups(filters)


@router.get("/groups/{board_group_id}")
async def get_board_group(
    board_group_id: int,
    board_group_service: BoardGroupService = Depends(get_board_group_service),
):
    return await board_group_service.get_board_group(board_group_id)


@router.put("/groups/{board_group_id}")
async def update_board_group(
    board_group_id: int,
    board_group_data: BoardGroupUpdate,
    current_user: dict = Depends(admin_required),
    board_group_service: BoardGroupService = Depends(get_board_group_service),
):
    return await board_group_service.update_board_group(board_group_id, board_group_data, current_user["id"])


@router.delete("/groups/{board_group_id}")
async def delete_board_group(
    board_group_id: int,
    current_user: dict = Depends(admin_required),
    board_group_service: BoardGroupService = Depends(get_board_group_service),
):
    return await board_group_service.delete_board_group(board_group_id, current_user["id"])


# ===== BOARD MEMBER ENDPOINTS =====

@router.post("/members")
async def create_board_member(
    form_data: Tuple[Dict[str, Any], Any] = Depends(get_board_member_multipart()),
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    json_data, image = form_data
    uploader = DirectFileUploader()
    image_url = await uploader.upload_file(image, "board_members")
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Ensure member_order has a valid value (>= 1)
    if "member_order" not in complete_data or complete_data.get("member_order", 0) < 1:
        complete_data["member_order"] = 1
    
    board_member_data = BoardMemberCreate(**complete_data)
    return await board_member_service.create_board_member(board_member_data, current_user["id"])


@router.get("/members")
async def get_board_members(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("member_order"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    filters = BoardMemberFilterParams(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await board_member_service.get_board_members(filters)


@router.get("/members/{board_member_id}")
async def get_board_member(
    board_member_id: int,
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    return await board_member_service.get_board_member(board_member_id)


@router.put("/members/{board_member_id}")
async def update_board_member(
    board_member_id: int,
    form_data: Tuple[Dict[str, Any], Optional[Any]] = Depends(get_board_member_multipart_update()),
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    json_data, image = form_data
    uploader = DirectFileUploader()
    image_url = await process_image_upload(image, "board_members", uploader)
    complete_data = merge_data_with_image_url(json_data, image_url)
    
    # Ensure member_order has a valid value if provided (>= 1)
    if "member_order" in complete_data and complete_data["member_order"] is not None and complete_data["member_order"] < 1:
        complete_data["member_order"] = 1
    
    board_member_data = BoardMemberUpdate(**complete_data)
    return await board_member_service.update_board_member(board_member_id, board_member_data, current_user["id"])


@router.delete("/members/{board_member_id}")
async def delete_board_member(
    board_member_id: int,
    current_user: dict = Depends(admin_required),
    board_member_service: BoardMemberService = Depends(get_board_member_service),
):
    return await board_member_service.delete_board_member(board_member_id, current_user["id"])