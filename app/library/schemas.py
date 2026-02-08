"""
CUSTOS Library Schemas
"""

from datetime import date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.library.models import BookCategory, BookStatus, BorrowStatus


# Book Create/Update
class BookCreate(BaseModel):
    isbn: Optional[str] = None
    title: str
    author: str
    publisher: Optional[str] = None
    category: BookCategory = BookCategory.OTHER
    subject: Optional[str] = None
    language: str = "English"
    publish_year: Optional[int] = None
    edition: Optional[str] = None
    pages: Optional[int] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    total_copies: int = 1
    location: Optional[str] = None


class BookUpdate(BaseModel):
    isbn: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    category: Optional[BookCategory] = None
    subject: Optional[str] = None
    language: Optional[str] = None
    publish_year: Optional[int] = None
    edition: Optional[str] = None
    pages: Optional[int] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    location: Optional[str] = None


class BookResponse(BaseModel):
    id: UUID
    isbn: Optional[str]
    title: str
    author: str
    publisher: Optional[str]
    category: BookCategory
    subject: Optional[str]
    language: str
    publish_year: Optional[int]
    edition: Optional[str]
    pages: Optional[int]
    description: Optional[str]
    cover_image_url: Optional[str]
    total_copies: int
    available_copies: int
    location: Optional[str]
    
    class Config:
        from_attributes = True


# Book Copy
class BookCopyCreate(BaseModel):
    book_id: UUID
    accession_number: str
    condition: str = "Good"
    acquisition_date: Optional[date] = None
    price: Optional[int] = None
    notes: Optional[str] = None


class BookCopyResponse(BaseModel):
    id: UUID
    book_id: UUID
    accession_number: str
    status: BookStatus
    condition: str
    acquisition_date: Optional[date]
    price: Optional[int]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# Borrow
class BorrowCreate(BaseModel):
    accession_number: str  # Can also borrow by accession number
    borrower_id: UUID
    due_days: int = Field(default=14, ge=1, le=90)


class BorrowReturn(BaseModel):
    accession_number: str
    fine_paid: bool = True
    notes: Optional[str] = None


class BorrowRecordResponse(BaseModel):
    id: UUID
    book_copy_id: UUID
    borrower_id: UUID
    issued_by: UUID
    status: BorrowStatus
    issue_date: date
    due_date: date
    return_date: Optional[date]
    fine_amount: int
    fine_paid: bool
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# Stats
class LibraryStats(BaseModel):
    total_books: int
    total_copies: int
    available_copies: int
    borrowed_copies: int
    overdue_count: int
    total_members: int
    books_issued_today: int
