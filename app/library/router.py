"""
CUSTOS Library Router
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.library.service import LibraryService
from app.library.schemas import BookCreate, BookUpdate, BorrowCreate, BorrowReturn


router = APIRouter(tags=["Library"])


# ========== Books ==========
@router.post("/books")
async def add_book(
    data: BookCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LIBRARY_MANAGE)),
):
    """Add a new book to the library catalog."""
    service = LibraryService(db, user.tenant_id)
    return await service.create_book(**data.model_dump())


@router.get("/books")
async def search_books(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = None,
    category: Optional[str] = None,
    available_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Search books in the library catalog."""
    service = LibraryService(db, user.tenant_id)
    books, total = await service.search_books(q, category, available_only, page, size)
    return {"items": books, "total": total, "page": page, "size": size}


@router.get("/books/{book_id}")
async def get_book(
    book_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get book details."""
    service = LibraryService(db, user.tenant_id)
    return await service.get_book(book_id)


@router.patch("/books/{book_id}")
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LIBRARY_MANAGE)),
):
    """Update book details."""
    service = LibraryService(db, user.tenant_id)
    return await service.update_book(book_id, **data.model_dump(exclude_unset=True))


# ========== Book Copies ==========
@router.post("/books/{book_id}/copies")
async def add_book_copy(
    book_id: UUID,
    accession_number: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    condition: str = "Good",
    _=Depends(require_permission(Permission.LIBRARY_MANAGE)),
):
    """Add a copy of a book."""
    service = LibraryService(db, user.tenant_id)
    return await service.add_book_copy(book_id, accession_number, condition=condition)


# ========== Borrowing ==========
@router.post("/issue")
async def issue_book(
    data: BorrowCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LIBRARY_ISSUE)),
):
    """Issue a book to a user."""
    service = LibraryService(db, user.tenant_id)
    return await service.issue_book(
        accession_number=data.accession_number,
        borrower_id=data.borrower_id,
        issued_by=user.user_id,
        due_days=data.due_days,
    )


@router.post("/return")
async def return_book(
    data: BorrowReturn,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LIBRARY_ISSUE)),
):
    """Return a borrowed book."""
    service = LibraryService(db, user.tenant_id)
    return await service.return_book(
        accession_number=data.accession_number,
        returned_to=user.user_id,
        fine_paid=data.fine_paid,
        notes=data.notes,
    )


@router.get("/overdue")
async def get_overdue_books(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    _=Depends(require_permission(Permission.LIBRARY_VIEW)),
):
    """Get all overdue books."""
    service = LibraryService(db, user.tenant_id)
    records, total = await service.get_overdue_books(page, size)
    return {"items": records, "total": total, "page": page, "size": size}


@router.get("/my-books")
async def get_my_borrowed_books(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get books currently borrowed by the logged-in user."""
    service = LibraryService(db, user.tenant_id)
    return await service.get_user_borrowed_books(user.user_id)


@router.get("/user/{user_id}/books")
async def get_user_borrowed_books(
    user_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LIBRARY_VIEW)),
):
    """Get books borrowed by a specific user."""
    service = LibraryService(db, user.tenant_id)
    return await service.get_user_borrowed_books(user_id)


@router.get("/stats")
async def get_library_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LIBRARY_VIEW)),
):
    """Get library statistics."""
    service = LibraryService(db, user.tenant_id)
    return await service.get_library_stats()
