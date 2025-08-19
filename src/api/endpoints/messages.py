"""Message management endpoints with public submission."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.message import MessageRepository
from src.services.message import MessageService
from src.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageListResponse,
    MessageSummary,
    MessageFilterParams,
    MessageStatusUpdate,
    PublicMessageResponse,
    MessageStatistics
)
from src.schemas.shared import MessageResponse as SharedMessageResponse
from src.models.message import MessageStatus
from src.auth.permissions import get_current_active_user, admin_required

router = APIRouter()


async def get_message_service(session: AsyncSession = Depends(get_db)) -> MessageService:
    """Get message service dependency."""
    message_repo = MessageRepository(session)
    return MessageService(message_repo)


# ===== PUBLIC ENDPOINTS =====

@router.post("/submit", response_model=PublicMessageResponse, summary="Submit a message (public)")
async def submit_message(
    message_data: MessageCreate,
    request: Request,
    message_service: MessageService = Depends(get_message_service),
):
    """
    Submit a message from the public.
    
    Public endpoint - no authentication required.
    Includes rate limiting, spam detection, and input sanitization.
    """
    return await message_service.submit_public_message(message_data, request)


# ===== ADMIN ENDPOINTS =====

@router.get("/", response_model=MessageListResponse, summary="Get messages with filters")
async def get_messages(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name, email, title, or message"),
    status: Optional[MessageStatus] = Query(None, description="Filter by message status"),
    unread_only: bool = Query(False, description="Show only unread messages"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get messages with filters and pagination.
    
    Requires admin role.
    """
    filters = MessageFilterParams(
        page=page,
        size=size,
        search=search,
        status=status,
        unread_only=unread_only,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await message_service.get_messages(filters)


@router.get("/unread", response_model=List[MessageResponse], summary="Get unread messages")
async def get_unread_messages(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get unread messages only.
    
    Requires admin role.
    """
    return await message_service.get_unread_messages(limit)




@router.get("/by-email/{email}", response_model=List[MessageResponse], summary="Get messages by email")
async def get_messages_by_email(
    email: str,
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get all messages from a specific email address.
    
    Requires admin role.
    """
    return await message_service.get_messages_by_email(email)


@router.get("/search", response_model=List[MessageResponse], summary="Search messages")
async def search_messages(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Search messages by content.
    
    Requires admin role.
    """
    return await message_service.search_messages(q, limit)


@router.get("/statistics", response_model=MessageStatistics, summary="Get message statistics")
async def get_message_statistics(
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get comprehensive message statistics.
    
    Requires admin role.
    """
    return await message_service.get_message_statistics()


@router.get("/summaries", response_model=List[MessageSummary], summary="Get message summaries")
async def get_message_summaries(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[MessageStatus] = Query(None, description="Filter by status"),
    unread_only: bool = Query(False, description="Show only unread messages"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get message summaries (lighter response).
    
    Requires admin role.
    """
    filters = MessageFilterParams(
        page=page,
        size=size,
        search=search,
        status=status,
        unread_only=unread_only,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await message_service.get_message_summaries(filters)


@router.get("/{message_id}", response_model=MessageResponse, summary="Get message by ID")
async def get_message(
    message_id: int,
    mark_as_read: bool = Query(False, description="Mark message as read when accessed"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get message by ID.
    
    Requires admin role. Optionally marks message as read.
    """
    return await message_service.get_message(message_id, mark_as_read, current_user["id"])


@router.put("/{message_id}", response_model=MessageResponse, summary="Update message")
async def update_message(
    message_id: int,
    message_data: MessageUpdate,
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Update message information.
    
    Requires admin role.
    """
    return await message_service.update_message(message_id, message_data, current_user["id"])


@router.delete("/{message_id}", response_model=SharedMessageResponse, summary="Delete message")
async def delete_message(
    message_id: int,
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Delete message (soft delete).
    
    Requires admin role.
    """
    return await message_service.delete_message(message_id, current_user["id"])


# ===== STATUS MANAGEMENT ENDPOINTS =====

@router.patch("/{message_id}/status", response_model=MessageResponse, summary="Update message status")
async def update_message_status(
    message_id: int,
    status_data: MessageStatusUpdate,
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Update message status.
    
    Requires admin role.
    """
    return await message_service.update_message_status(message_id, status_data, current_user["id"])




@router.post("/{message_id}/mark-read", response_model=MessageResponse, summary="Mark message as read")
async def mark_message_as_read(
    message_id: int,
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Mark message as read.
    
    Requires admin role.
    """
    status_data = MessageStatusUpdate(status=MessageStatus.READ)
    return await message_service.update_message_status(message_id, status_data, current_user["id"])




@router.post("/{message_id}/archive", response_model=MessageResponse, summary="Archive message")
async def archive_message(
    message_id: int,
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Archive message.
    
    Requires admin role.
    """
    status_data = MessageStatusUpdate(status=MessageStatus.ARCHIVED)
    return await message_service.update_message_status(message_id, status_data, current_user["id"])


# ===== BULK OPERATIONS =====

@router.post("/bulk/status", response_model=SharedMessageResponse, summary="Bulk update message status")
async def bulk_update_status(
    message_ids: List[int] = Body(..., description="List of message IDs"),
    status: MessageStatus = Body(..., description="New status for all messages"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Bulk update message status.
    
    Requires admin role.
    """
    return await message_service.bulk_update_status(message_ids, status, current_user["id"])




@router.post("/bulk/delete", response_model=SharedMessageResponse, summary="Bulk delete messages")
async def bulk_delete_messages(
    message_ids: List[int] = Body(..., description="List of message IDs to delete"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Bulk delete messages.
    
    Requires admin role.
    """
    return await message_service.bulk_delete(message_ids, current_user["id"])


@router.post("/bulk/mark-read", response_model=SharedMessageResponse, summary="Bulk mark messages as read")
async def bulk_mark_as_read(
    message_ids: List[int] = Body(..., description="List of message IDs"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Bulk mark messages as read.
    
    Requires admin role.
    """
    return await message_service.bulk_update_status(message_ids, MessageStatus.READ, current_user["id"])


@router.post("/bulk/archive", response_model=SharedMessageResponse, summary="Bulk archive messages")
async def bulk_archive_messages(
    message_ids: List[int] = Body(..., description="List of message IDs"),
    current_user: dict = Depends(admin_required),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Bulk archive messages.
    
    Requires admin role.
    """
    return await message_service.bulk_update_status(message_ids, MessageStatus.ARCHIVED, current_user["id"])