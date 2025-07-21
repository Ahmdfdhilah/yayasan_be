#!/usr/bin/env python3
"""Fix file paths in existing media_files records."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.core.database import async_session
from src.models.media_file import MediaFile


async def fix_file_paths():
    """Fix file paths to use forward slashes and consistent upload directory."""
    
    async with async_session() as session:
        try:
            # Get all media files
            result = await session.execute(
                text("SELECT id, file_path, file_metadata FROM media_files WHERE deleted_at IS NULL")
            )
            files = result.fetchall()
            
            print(f"Found {len(files)} files to process...")
            
            updated_count = 0
            
            for file_record in files:
                file_id, file_path, file_metadata = file_record
                
                # Convert backslashes to forward slashes
                new_path = file_path.replace("\\", "/")
                
                # Ensure path starts with static/uploads
                if new_path.startswith("uploads/"):
                    new_path = "static/" + new_path
                elif not new_path.startswith("static/uploads/"):
                    # Extract filename and put in correct directory
                    filename = Path(new_path).name
                    new_path = f"static/uploads/{filename}"
                
                # Update metadata if needed
                new_metadata = file_metadata
                if file_metadata and isinstance(file_metadata, dict):
                    if "upload_path" in file_metadata:
                        new_metadata = file_metadata.copy()
                        new_metadata["upload_path"] = new_metadata["upload_path"].replace("\\", "/")
                        if new_metadata["upload_path"] == "uploads":
                            new_metadata["upload_path"] = "static/uploads"
                
                # Update if path changed
                if new_path != file_path or new_metadata != file_metadata:
                    await session.execute(
                        text("""
                            UPDATE media_files 
                            SET file_path = :new_path, 
                                file_metadata = :new_metadata,
                                updated_at = NOW()
                            WHERE id = :file_id
                        """),
                        {
                            "new_path": new_path,
                            "new_metadata": json.dumps(new_metadata) if new_metadata else None,
                            "file_id": file_id
                        }
                    )
                    updated_count += 1
                    print(f"Updated file {file_id}: {file_path} -> {new_path}")
            
            await session.commit()
            print(f"✅ Successfully updated {updated_count} file paths")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error fixing file paths: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(fix_file_paths())