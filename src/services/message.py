"""Message service for business logic with sanitization and rate limiting."""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, Request
from datetime import datetime, timedelta

from src.repositories.message import MessageRepository
from src.schemas.message import (
    MessageCreate, MessageUpdate, MessageResponse, MessageListResponse,
    MessageSummary, MessageFilterParams, MessageStatusUpdate,
    PublicMessageResponse, MessageStatistics
)
from src.schemas.shared import MessageResponse as SharedMessageResponse
from src.models.message import MessageStatus


class MessageService:
    """Message service for business logic with sanitization and rate limiting."""
    
    def __init__(self, message_repo: MessageRepository):
        self.message_repo = message_repo
    
    # ===== PUBLIC MESSAGE SUBMISSION =====
    
    async def submit_public_message(self, message_data: MessageCreate, request: Request) -> PublicMessageResponse:
        """Submit a message from public (with rate limiting and sanitization)."""
        # Get client info for tracking
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]  # Limit length
        
        # Rate limiting check
        await self._check_rate_limit(ip_address, message_data.email)
        
        # Additional validation for public submissions
        await self._validate_public_submission(message_data, ip_address)
        
        # Create message (sanitization is handled in schema validators)
        message = await self.message_repo.create(
            message_data, 
            ip_address=ip_address, 
            user_agent=user_agent
        )
        
        return PublicMessageResponse.from_message_model(message)
    
    # ===== ADMIN MESSAGE MANAGEMENT =====
    
    async def get_message(self, message_id: int, mark_as_read: bool = False, read_by: Optional[int] = None) -> MessageResponse:
        """Get message by ID (optionally mark as read)."""
        message = await self.message_repo.get_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Mark as read if requested and currently unread
        if mark_as_read and message.is_unread:
            await self.message_repo.update_status(
                message_id, 
                MessageStatus.READ, 
                read_by
            )
            # Refresh message to get updated data
            message = await self.message_repo.get_by_id(message_id)
        
        return MessageResponse.from_message_model(message)
    
    async def update_message(self, message_id: int, message_data: MessageUpdate, updated_by: Optional[int] = None) -> MessageResponse:
        """Update message information (admin only)."""
        # Check if message exists
        existing_message = await self.message_repo.get_by_id(message_id)
        if not existing_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Update message in database
        updated_message = await self.message_repo.update(message_id, message_data, updated_by)
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message"
            )
        
        return MessageResponse.from_message_model(updated_message)
    
    async def delete_message(self, message_id: int, deleted_by: Optional[int] = None) -> SharedMessageResponse:
        """Delete message (soft delete)."""
        # Check if message exists
        existing_message = await self.message_repo.get_by_id(message_id)
        if not existing_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Soft delete message
        success = await self.message_repo.soft_delete(message_id, deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete message"
            )
        
        return SharedMessageResponse(message="Message deleted successfully")
    
    async def get_messages(self, filters: MessageFilterParams) -> MessageListResponse:
        """Get messages with filters and pagination."""
        messages, total = await self.message_repo.get_all_filtered(filters)
        
        message_responses = [MessageResponse.from_message_model(message) for message in messages]
        
        return MessageListResponse(
            items=message_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size
        )
    
    # ===== MESSAGE STATUS MANAGEMENT =====
    
    async def update_message_status(self, message_id: int, status_data: MessageStatusUpdate, updated_by: Optional[int] = None) -> MessageResponse:
        """Update message status."""
        # Check if message exists
        existing_message = await self.message_repo.get_by_id(message_id)
        if not existing_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Update status
        updated_message = await self.message_repo.update_status(
            message_id, 
            status_data.status, 
            updated_by
        )
        
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message status"
            )
        
        return MessageResponse.from_message_model(updated_message)
    
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_status(self, message_ids: List[int], status: MessageStatus, updated_by: Optional[int] = None) -> SharedMessageResponse:
        """Bulk update message status."""
        if not message_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No message IDs provided"
            )
        
        updated_count = await self.message_repo.bulk_update_status(message_ids, status, updated_by)
        
        return SharedMessageResponse(
            message=f"{updated_count} message(s) status updated to {status.value}"
        )
    
    
    async def bulk_delete(self, message_ids: List[int], deleted_by: Optional[int] = None) -> SharedMessageResponse:
        """Bulk delete messages."""
        if not message_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No message IDs provided"
            )
        
        deleted_count = await self.message_repo.bulk_delete(message_ids, deleted_by)
        
        return SharedMessageResponse(
            message=f"{deleted_count} message(s) deleted successfully"
        )
    
    # ===== SPECIALIZED QUERIES =====
    
    async def get_unread_messages(self, limit: Optional[int] = None) -> List[MessageResponse]:
        """Get unread messages."""
        messages = await self.message_repo.get_unread_messages(limit)
        return [MessageResponse.from_message_model(message) for message in messages]
    
    
    async def get_messages_by_email(self, email: str) -> List[MessageResponse]:
        """Get all messages from specific email address."""
        messages = await self.message_repo.get_messages_by_email(email)
        return [MessageResponse.from_message_model(message) for message in messages]
    
    
    async def search_messages(self, search_term: str, limit: Optional[int] = None) -> List[MessageResponse]:
        """Search messages by content."""
        messages = await self.message_repo.search_messages(search_term, limit)
        return [MessageResponse.from_message_model(message) for message in messages]
    
    async def get_message_summaries(self, filters: MessageFilterParams) -> List[MessageSummary]:
        """Get message summaries (lighter response)."""
        messages, _ = await self.message_repo.get_all_filtered(filters)
        return [MessageSummary.from_message_model(message) for message in messages]
    
    async def get_message_statistics(self) -> MessageStatistics:
        """Get comprehensive message statistics."""
        stats_data = await self.message_repo.get_message_statistics()
        return MessageStatistics(**stats_data)
    
    # ===== PRIVATE HELPER METHODS =====
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    async def _check_rate_limit(self, ip_address: Optional[str], email: str) -> None:
        """Check rate limiting for message submissions."""
        # Time window for rate limiting (e.g., last hour)
        time_window = datetime.utcnow() - timedelta(hours=1)
        
        # Check IP-based rate limiting
        if ip_address:
            # This is a simplified check - in production you'd use Redis or similar
            # For now, we'll implement basic database-based checking
            pass  # Implement as needed
        
        # Check email-based rate limiting
        recent_messages = await self.message_repo.get_messages_by_email(email)
        recent_in_window = [
            msg for msg in recent_messages 
            if msg.created_at and msg.created_at >= time_window
        ]
        
        # Allow max 5 messages per email per hour
        if len(recent_in_window) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many messages submitted. Please wait before sending another message."
            )
    
    async def _validate_public_submission(self, message_data: MessageCreate, ip_address: Optional[str]) -> None:
        """Additional validation for public message submissions."""
        # Check for spam indicators
        spam_keywords = [
            "viagra", "casino", "lottery", "winner", "congratulations",
            "click here", "free money", "get rich", "work from home"
        ]
        
        message_text = (message_data.message + " " + message_data.title).lower()
        spam_score = sum(1 for keyword in spam_keywords if keyword in message_text)
        
        if spam_score >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message appears to be spam and was rejected."
            )
        
        # Check message length (very long messages might be spam)
        if len(message_data.message) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is too long. Please keep it under 5000 characters."
            )
        
        # Check for excessive links
        link_count = message_text.count("http://") + message_text.count("https://") + message_text.count("www.")
        if link_count > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message contains too many links and was rejected."
            )