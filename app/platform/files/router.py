"""
CUSTOS File Router
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser
from app.platform.files.service import FileService


router = APIRouter(tags=["Files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = None,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload file."""
    service = FileService(db, user.tenant_id)
    result = await service.upload(file, user.user_id, folder)
    return result


@router.post("/upload-multiple")
async def upload_multiple(
    files: list[UploadFile] = File(...),
    folder: Optional[str] = None,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple files."""
    service = FileService(db, user.tenant_id)
    results = []
    for file in files:
        result = await service.upload(file, user.user_id, folder)
        results.append(result)
    return {"files": results}


@router.get("/download")
async def download_file(
    path: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Download file."""
    service = FileService(db, user.tenant_id)
    file_path = service.get_file_path(path)
    
    if not file_path:
        return {"error": "File not found"}
    
    return FileResponse(path=file_path)


@router.delete("")
async def delete_file(
    path: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete file."""
    service = FileService(db, user.tenant_id)
    success = service.delete_file(path)
    return {"success": success}


@router.get("/usage")
async def get_storage_usage(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get storage usage."""
    service = FileService(db, user.tenant_id)
    return service.get_storage_usage()
