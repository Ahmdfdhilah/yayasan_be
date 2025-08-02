"""Program repository for database operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update

from src.models.program import Program
from src.schemas.program import ProgramCreate, ProgramUpdate


class ProgramRepository:
    """Repository for program operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, program_data: ProgramCreate) -> Program:
        """Create a new program."""
        program = Program(**program_data.dict())
        self.session.add(program)
        await self.session.commit()
        await self.session.refresh(program)
        return program

    async def get_by_id(self, program_id: int) -> Optional[Program]:
        """Get program by ID."""
        query = select(Program).where(Program.id == program_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[Program], int]:
        """Get all programs with pagination and search."""
        query = select(Program)
        count_query = select(func.count(Program.id))
        
        # Apply search filter
        if search:
            search_filter = or_(
                Program.title.ilike(f"%{search}%"),
                Program.excerpt.ilike(f"%{search}%"),
                Program.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        programs = result.scalars().all()
        
        return list(programs), total

    async def update(self, program_id: int, update_data: ProgramUpdate) -> Optional[Program]:
        """Update program."""
        # Get existing program
        program = await self.get_by_id(program_id)
        if not program:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(program, field, value)
        
        await self.session.commit()
        await self.session.refresh(program)
        return program

    async def delete(self, program_id: int) -> bool:
        """Delete program."""
        query = delete(Program).where(Program.id == program_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def get_by_title(self, title: str) -> Optional[Program]:
        """Get program by title."""
        query = select(Program).where(Program.title == title)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()