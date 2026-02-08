"""
CUSTOS Library Models
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class BookCategory(str, Enum):
    TEXTBOOK = "textbook"
    REFERENCE = "reference"
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    SCIENCE = "science"
    HISTORY = "history"
    BIOGRAPHY = "biography"
    MAGAZINE = "magazine"
    JOURNAL = "journal"
    OTHER = "other"


class BookStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    LOST = "lost"


class BorrowStatus(str, Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


class Book(TenantBaseModel):
    """Book in library catalog."""
    __tablename__ = "library_books"
    
    isbn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    publisher: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    category: Mapped[BookCategory] = mapped_column(SQLEnum(BookCategory), default=BookCategory.OTHER)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="English")
    
    publish_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, default=1)
    
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Shelf/rack
    
    # Relationships
    copies: Mapped[List["BookCopy"]] = relationship("BookCopy", back_populates="book")


class BookCopy(TenantBaseModel):
    """Individual copy of a book."""
    __tablename__ = "library_book_copies"
    
    book_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("library_books.id"))
    
    accession_number: Mapped[str] = mapped_column(String(50), unique=True)  # Unique ID for this copy
    status: Mapped[BookStatus] = mapped_column(SQLEnum(BookStatus), default=BookStatus.AVAILABLE)
    
    condition: Mapped[str] = mapped_column(String(50), default="Good")  # Good, Fair, Poor
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In paise/cents
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    book: Mapped["Book"] = relationship("Book", back_populates="copies")
    borrow_records: Mapped[List["BorrowRecord"]] = relationship("BorrowRecord", back_populates="book_copy")


class BorrowRecord(TenantBaseModel):
    """Book borrowing record."""
    __tablename__ = "library_borrow_records"
    
    book_copy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("library_book_copies.id"))
    borrower_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    issued_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    status: Mapped[BorrowStatus] = mapped_column(SQLEnum(BorrowStatus), default=BorrowStatus.ACTIVE)
    
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    returned_to: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    
    fine_amount: Mapped[int] = mapped_column(Integer, default=0)  # In paise
    fine_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    book_copy: Mapped["BookCopy"] = relationship("BookCopy", back_populates="borrow_records")
