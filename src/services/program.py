"""Program business logic services."""

from typing import List, Optional
from fastapi import HTTPException, status

from src.repositories.program import ProgramRepository
from src.schemas.program import ProgramCreate, ProgramUpdate, ProgramResponse, ProgramListResponse, ProgramFilterParams
from src.schemas.shared import MessageResponse


class ProgramService:
    """Service for program business logic."""

    def __init__(self, program_repo: ProgramRepository):
        self.program_repo = program_repo

    async def create_program(self, program_data: ProgramCreate) -> ProgramResponse:
        """Create a new program."""
        # Check if title already exists
        existing = await self.program_repo.get_by_title(program_data.title)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program with this title already exists"
            )
        
        program = await self.program_repo.create(program_data)
        return ProgramResponse.model_validate(program)

    async def get_program(self, program_id: int) -> ProgramResponse:
        """Get program by ID."""
        program = await self.program_repo.get_by_id(program_id)
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        return ProgramResponse.model_validate(program)

    async def get_all_programs(
        self,
        filters: ProgramFilterParams
    ) -> ProgramListResponse:
        """Get all programs with pagination and search."""
        programs, total = await self.program_repo.get_all(
            skip=filters.skip,
            limit=filters.limit,
            search=filters.search
        )
        
        return ProgramListResponse(
            items=[ProgramResponse.model_validate(program) for program in programs],
            total=total,
            page=(filters.skip // filters.limit) + 1,
            size=filters.limit,
            pages=(total + filters.limit - 1) // filters.limit
        )

    async def update_program(
        self, 
        program_id: int, 
        update_data: ProgramUpdate
    ) -> ProgramResponse:
        """Update program."""
        # Check if program exists
        existing = await self.program_repo.get_by_id(program_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        # Check if new title conflicts with another program
        if update_data.title and update_data.title != existing.title:
            title_conflict = await self.program_repo.get_by_title(update_data.title)
            if title_conflict and title_conflict.id != program_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Program with this title already exists"
                )
        
        updated_program = await self.program_repo.update(program_id, update_data)
        return ProgramResponse.model_validate(updated_program)

    async def delete_program(self, program_id: int) -> MessageResponse:
        """Delete program."""
        # Check if program exists
        existing = await self.program_repo.get_by_id(program_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        deleted = await self.program_repo.delete(program_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete program"
            )
        
        return MessageResponse(message="Program deleted successfully")