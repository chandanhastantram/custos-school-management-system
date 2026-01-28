"""
CUSTOS File Upload Service
"""

import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
    "video": [".mp4", ".webm", ".mov"],
    "audio": [".mp3", ".wav", ".ogg"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class FileService:
    """File upload and storage."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.storage_path = Path(settings.storage_path)
    
    def _get_tenant_path(self) -> Path:
        path = self.storage_path / str(self.tenant_id)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_extension(self, filename: str) -> str:
        return Path(filename).suffix.lower()
    
    def _get_category(self, extension: str) -> Optional[str]:
        for category, extensions in ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return category
        return None
    
    async def upload(
        self,
        file: UploadFile,
        uploaded_by: UUID,
        folder: Optional[str] = None,
    ) -> dict:
        """Upload file."""
        ext = self._get_extension(file.filename)
        category = self._get_category(ext)
        
        if not category:
            raise ValidationError(f"File type {ext} not allowed")
        
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise ValidationError(f"File too large. Max: {MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Generate unique filename
        new_filename = f"{uuid4().hex}{ext}"
        
        # Create folder
        storage_dir = self._get_tenant_path()
        if folder:
            storage_dir = storage_dir / folder
            storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_dir / new_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Calculate hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        relative_path = str(file_path.relative_to(self.storage_path))
        
        return {
            "original_name": file.filename,
            "stored_name": new_filename,
            "path": relative_path,
            "size_bytes": len(content),
            "mime_type": file.content_type,
            "category": category,
            "hash": file_hash,
        }
    
    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """Get full file path."""
        full_path = self.storage_path / relative_path
        if full_path.exists():
            return full_path
        return None
    
    def delete_file(self, relative_path: str) -> bool:
        """Delete file."""
        full_path = self.storage_path / relative_path
        if full_path.exists():
            os.remove(full_path)
            return True
        return False
    
    def get_storage_usage(self) -> dict:
        """Get storage usage for tenant."""
        tenant_path = self._get_tenant_path()
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(tenant_path):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_bytes": total_size,
            "total_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
        }
