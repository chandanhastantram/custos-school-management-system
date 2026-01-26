"""
CUSTOS File Service

File upload and storage management.
"""

import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.models.audit import FileUpload


# Allowed file extensions by category
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
    "video": [".mp4", ".webm", ".mov"],
    "audio": [".mp3", ".wav", ".ogg"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class FileService:
    """File upload and storage service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.storage_path = Path(settings.storage_path)
    
    def _get_tenant_path(self) -> Path:
        """Get tenant's storage directory."""
        path = self.storage_path / str(self.tenant_id)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension."""
        return Path(filename).suffix.lower()
    
    def _get_file_category(self, extension: str) -> Optional[str]:
        """Get file category from extension."""
        for category, extensions in ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return category
        return None
    
    def _generate_filename(self, original: str) -> str:
        """Generate unique filename."""
        ext = self._get_file_extension(original)
        return f"{uuid4().hex}{ext}"
    
    def _calculate_hash(self, content: bytes) -> str:
        """Calculate file hash."""
        return hashlib.sha256(content).hexdigest()
    
    async def upload_file(
        self,
        file: UploadFile,
        uploaded_by: UUID,
        folder: Optional[str] = None,
    ) -> FileUpload:
        """Upload file."""
        # Validate extension
        ext = self._get_file_extension(file.filename)
        category = self._get_file_category(ext)
        
        if not category:
            raise ValidationError(f"File type {ext} not allowed")
        
        # Read content
        content = await file.read()
        
        # Validate size
        if len(content) > MAX_FILE_SIZE:
            raise ValidationError(f"File too large. Max: {MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Generate filename and path
        new_filename = self._generate_filename(file.filename)
        
        # Create folder if specified
        storage_dir = self._get_tenant_path()
        if folder:
            storage_dir = storage_dir / folder
            storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_dir / new_filename
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Calculate hash
        file_hash = self._calculate_hash(content)
        
        # Create record
        relative_path = str(file_path.relative_to(self.storage_path))
        
        file_record = FileUpload(
            tenant_id=self.tenant_id,
            uploaded_by=uploaded_by,
            original_name=file.filename,
            stored_name=new_filename,
            path=relative_path,
            size_bytes=len(content),
            mime_type=file.content_type,
            category=category,
            hash=file_hash,
        )
        
        self.session.add(file_record)
        await self.session.commit()
        await self.session.refresh(file_record)
        
        return file_record
    
    async def get_file(self, file_id: UUID) -> Optional[FileUpload]:
        """Get file record."""
        query = select(FileUpload).where(
            FileUpload.tenant_id == self.tenant_id,
            FileUpload.id == file_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_file_path(self, file_id: UUID) -> Optional[Path]:
        """Get full file path."""
        file_record = await self.get_file(file_id)
        if not file_record:
            return None
        
        return self.storage_path / file_record.path
    
    async def delete_file(self, file_id: UUID) -> bool:
        """Delete file."""
        file_record = await self.get_file(file_id)
        if not file_record:
            return False
        
        # Delete physical file
        file_path = self.storage_path / file_record.path
        if file_path.exists():
            os.remove(file_path)
        
        # Delete record
        await self.session.delete(file_record)
        await self.session.commit()
        
        return True
    
    async def list_files(
        self,
        category: Optional[str] = None,
        uploaded_by: Optional[UUID] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[FileUpload], int]:
        """List uploaded files."""
        from sqlalchemy import func
        
        query = select(FileUpload).where(FileUpload.tenant_id == self.tenant_id)
        
        if category:
            query = query.where(FileUpload.category == category)
        if uploaded_by:
            query = query.where(FileUpload.uploaded_by == uploaded_by)
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(FileUpload.created_at.desc())
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_storage_usage(self) -> dict:
        """Get storage usage for tenant."""
        from sqlalchemy import func
        
        query = select(func.sum(FileUpload.size_bytes)).where(
            FileUpload.tenant_id == self.tenant_id
        )
        result = await self.session.execute(query)
        total_bytes = result.scalar() or 0
        
        count_query = select(func.count()).select_from(FileUpload).where(
            FileUpload.tenant_id == self.tenant_id
        )
        count_result = await self.session.execute(count_query)
        file_count = count_result.scalar() or 0
        
        return {
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "file_count": file_count,
        }
