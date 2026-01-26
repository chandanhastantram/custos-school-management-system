"""
CUSTOS File Upload API Endpoints

File upload routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx
from app.services.file_service import FileService
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload file."""
    service = FileService(db, ctx.tenant_id)
    file_record = await service.upload_file(file, ctx.user.user_id, folder)
    
    return {
        "id": str(file_record.id),
        "original_name": file_record.original_name,
        "size_bytes": file_record.size_bytes,
        "category": file_record.category,
        "path": file_record.path,
    }


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    folder: Optional[str] = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple files."""
    service = FileService(db, ctx.tenant_id)
    
    results = []
    for file in files:
        file_record = await service.upload_file(file, ctx.user.user_id, folder)
        results.append({
            "id": str(file_record.id),
            "original_name": file_record.original_name,
            "size_bytes": file_record.size_bytes,
        })
    
    return {"files": results}


@router.get("/{file_id}")
async def get_file_info(
    file_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get file metadata."""
    service = FileService(db, ctx.tenant_id)
    file_record = await service.get_file(file_id)
    
    if not file_record:
        return {"error": "File not found"}
    
    return {
        "id": str(file_record.id),
        "original_name": file_record.original_name,
        "size_bytes": file_record.size_bytes,
        "mime_type": file_record.mime_type,
        "category": file_record.category,
        "created_at": str(file_record.created_at),
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Download file."""
    service = FileService(db, ctx.tenant_id)
    file_record = await service.get_file(file_id)
    
    if not file_record:
        return {"error": "File not found"}
    
    file_path = await service.get_file_path(file_id)
    
    if not file_path or not file_path.exists():
        return {"error": "File not found on disk"}
    
    return FileResponse(
        path=file_path,
        filename=file_record.original_name,
        media_type=file_record.mime_type,
    )


@router.delete("/{file_id}", response_model=SuccessResponse)
async def delete_file(
    file_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Delete file."""
    service = FileService(db, ctx.tenant_id)
    success = await service.delete_file(file_id)
    return SuccessResponse(success=success, message="Deleted" if success else "Not found")


@router.get("")
async def list_files(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List uploaded files."""
    service = FileService(db, ctx.tenant_id)
    files, total = await service.list_files(category=category, page=page, size=size)
    
    return {
        "items": [
            {
                "id": str(f.id),
                "original_name": f.original_name,
                "size_bytes": f.size_bytes,
                "category": f.category,
            }
            for f in files
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/storage/usage")
async def get_storage_usage(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get storage usage for tenant."""
    service = FileService(db, ctx.tenant_id)
    return await service.get_storage_usage()
