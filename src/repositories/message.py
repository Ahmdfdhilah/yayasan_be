"""Message repository for CRUD operations."""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.message import Message, MessageStatus
from src.schemas.message import MessageCreate, MessageUpdate, MessageFilterParams


class MessageRepository:
    """Message repository for CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ===== BASIC CRUD OPERATIONS =====
    
    async def create(self, message_data: MessageCreate, ip_address: Optional[str] = None, user_agent: Optional[str] = None, created_by: Optional[int] = None) -> Message:
        """Create a new message."""
        message = Message(
            email=message_data.email,
            name=message_data.name,
            title=message_data.title,
            message=message_data.message,
            status=MessageStatus.UNREAD,
            ip_address=ip_address,
            user_agent=user_agent,
            created_by=created_by
        )
        
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID."""
        query = select(Message).where(
            and_(Message.id == message_id, Message.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, message_id: int, message_data: MessageUpdate, updated_by: Optional[int] = None) -> Optional[Message]:
        """Update message information."""
        message = await self.get_by_id(message_id)
        if not message:
            return None
        
        # Update fields
        update_data = message_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(message, key, value)
        
        message.updated_at = datetime.utcnow()
        message.updated_by = updated_by
        
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def soft_delete(self, message_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete message."""
        query = (
            update(Message)
            .where(Message.id == message_id)
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def hard_delete(self, message_id: int) -> bool:
        """Permanently delete message."""
        query = delete(Message).where(Message.id == message_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # ===== FILTERING AND LISTING =====
    
    async def get_all_filtered(self, filters: MessageFilterParams) -> Tuple[List[Message], int]:
        """Get messages with filters and pagination."""
        # Base query
        query = select(Message).where(Message.deleted_at.is_(None))
        count_query = select(func.count(Message.id)).where(Message.deleted_at.is_(None))
        
        # Apply filters
        if filters.search:
            search_filter = or_(
                Message.name.ilike(f"%{filters.search}%"),
                Message.email.ilike(f"%{filters.search}%"),
                Message.title.ilike(f"%{filters.search}%"),
                Message.message.ilike(f"%{filters.search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.status:
            query = query.where(Message.status == filters.status)
            count_query = count_query.where(Message.status == filters.status)
        
        if filters.unread_only:
            query = query.where(Message.status == MessageStatus.UNREAD)
            count_query = count_query.where(Message.status == MessageStatus.UNREAD)
        
        if filters.created_after:
            query = query.where(Message.created_at >= filters.created_after)
            count_query = count_query.where(Message.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(Message.created_at <= filters.created_before)
            count_query = count_query.where(Message.created_at <= filters.created_before)
        
        # Apply sorting
        if filters.sort_by == "name":
            sort_column = Message.name
        elif filters.sort_by == "email":
            sort_column = Message.email
        elif filters.sort_by == "title":
            sort_column = Message.title
        elif filters.sort_by == "status":
            sort_column = Message.status
        elif filters.sort_by == "updated_at":
            sort_column = Message.updated_at
        else:
            sort_column = Message.created_at
        
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.size
        query = query.offset(offset).limit(filters.size)
        
        # Execute queries
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return list(messages), total
    
    # ===== STATUS MANAGEMENT =====
    
    async def update_status(self, message_id: int, status: MessageStatus, updated_by: Optional[int] = None) -> Optional[Message]:
        """Update message status."""
        message = await self.get_by_id(message_id)
        if not message:
            return None
        
        old_status = message.status
        message.status = status
        message.updated_at = datetime.utcnow()
        message.updated_by = updated_by
        
        # Set timestamps based on status
        if status == MessageStatus.READ and old_status == MessageStatus.UNREAD:
            message.read_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    
    # ===== BULK OPERATIONS =====
    
    async def bulk_update_status(self, message_ids: List[int], status: MessageStatus, updated_by: Optional[int] = None) -> int:
        """Bulk update message status."""
        update_values = {
            "status": status,
            "updated_at": datetime.utcnow(),
            "updated_by": updated_by
        }
        
        # Add timestamp based on status
        if status == MessageStatus.READ:
            update_values["read_at"] = datetime.utcnow()
        
        query = (
            update(Message)
            .where(Message.id.in_(message_ids))
            .values(**update_values)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    
    async def bulk_delete(self, message_ids: List[int], deleted_by: Optional[int] = None) -> int:
        """Bulk soft delete messages."""
        query = (
            update(Message)
            .where(Message.id.in_(message_ids))
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
    
    # ===== STATISTICS AND QUERIES =====
    
    async def get_unread_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get unread messages."""
        query = select(Message).where(
            and_(
                Message.deleted_at.is_(None),
                Message.status == MessageStatus.UNREAD
            )
        ).order_by(Message.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    
    async def get_messages_by_email(self, email: str) -> List[Message]:
        """Get all messages from specific email address."""
        query = select(Message).where(
            and_(
                Message.deleted_at.is_(None),
                Message.email == email.lower()
            )
        ).order_by(Message.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    
    async def get_message_statistics(self) -> Dict[str, Any]:
        """Get comprehensive message statistics."""
        # Total messages
        total_query = select(func.count(Message.id)).where(Message.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_messages = total_result.scalar()
        
        # Messages by status
        status_query = (
            select(Message.status, func.count(Message.id))
            .where(Message.deleted_at.is_(None))
            .group_by(Message.status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = dict(status_result.fetchall())
        
        # Time-based statistics
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)
        
        # Messages today
        today_query = select(func.count(Message.id)).where(
            and_(
                Message.deleted_at.is_(None),
                Message.created_at >= today_start
            )
        )
        today_result = await self.session.execute(today_query)
        messages_today = today_result.scalar()
        
        # Messages this week
        week_query = select(func.count(Message.id)).where(
            and_(
                Message.deleted_at.is_(None),
                Message.created_at >= week_start
            )
        )
        week_result = await self.session.execute(week_query)
        messages_this_week = week_result.scalar()
        
        # Messages this month
        month_query = select(func.count(Message.id)).where(
            and_(
                Message.deleted_at.is_(None),
                Message.created_at >= month_start
            )
        )
        month_result = await self.session.execute(month_query)
        messages_this_month = month_result.scalar()
        
        return {
            "total_messages": total_messages,
            "unread_messages": status_counts.get(MessageStatus.UNREAD, 0),
            "read_messages": status_counts.get(MessageStatus.READ, 0),
            "archived_messages": status_counts.get(MessageStatus.ARCHIVED, 0),
            "messages_today": messages_today,
            "messages_this_week": messages_this_week,
            "messages_this_month": messages_this_month
        }
    
    async def search_messages(self, search_term: str, limit: Optional[int] = None) -> List[Message]:
        """Search messages by content."""
        query = select(Message).where(
            and_(
                Message.deleted_at.is_(None),
                or_(
                    Message.name.ilike(f"%{search_term}%"),
                    Message.email.ilike(f"%{search_term}%"),
                    Message.title.ilike(f"%{search_term}%"),
                    Message.message.ilike(f"%{search_term}%")
                )
            )
        ).order_by(Message.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())