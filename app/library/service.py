"""
CUSTOS Library Service
"""

from datetime import date, datetime, timezone, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.library.models import Book, BookCopy, BorrowRecord, BookStatus, BorrowStatus


class LibraryService:
    """Library management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ========== Books ==========
    async def create_book(
        self,
        title: str,
        author: str,
        **kwargs,
    ) -> Book:
        """Add a new book to catalog."""
        book = Book(
            tenant_id=self.tenant_id,
            title=title,
            author=author,
            available_copies=kwargs.get("total_copies", 1),
            **kwargs,
        )
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book
    
    async def update_book(self, book_id: UUID, **updates) -> Book:
        """Update book details."""
        book = await self.get_book(book_id)
        for key, value in updates.items():
            if value is not None and hasattr(book, key):
                setattr(book, key, value)
        await self.session.commit()
        return book
    
    async def get_book(self, book_id: UUID) -> Book:
        """Get book by ID."""
        query = select(Book).where(
            Book.tenant_id == self.tenant_id,
            Book.id == book_id,
        ).options(selectinload(Book.copies))
        result = await self.session.execute(query)
        book = result.scalar_one_or_none()
        if not book:
            raise ResourceNotFoundError("Book", str(book_id))
        return book
    
    async def search_books(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        available_only: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Book], int]:
        """Search books in catalog."""
        stmt = select(Book).where(
            Book.tenant_id == self.tenant_id,
            Book.is_deleted == False,
        )
        
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                    Book.isbn.ilike(search_pattern),
                )
            )
        
        if category:
            stmt = stmt.where(Book.category == category)
        
        if available_only:
            stmt = stmt.where(Book.available_copies > 0)
        
        # Count
        count_query = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        stmt = stmt.order_by(Book.title).offset(skip).limit(size)
        result = await self.session.execute(stmt)
        
        return list(result.scalars().all()), total
    
    # ========== Book Copies ==========
    async def add_book_copy(
        self,
        book_id: UUID,
        accession_number: str,
        **kwargs,
    ) -> BookCopy:
        """Add a copy of a book."""
        book = await self.get_book(book_id)
        
        copy = BookCopy(
            tenant_id=self.tenant_id,
            book_id=book_id,
            accession_number=accession_number,
            **kwargs,
        )
        self.session.add(copy)
        
        # Update book counts
        book.total_copies += 1
        book.available_copies += 1
        
        await self.session.commit()
        await self.session.refresh(copy)
        return copy
    
    async def get_copy_by_accession(self, accession_number: str) -> BookCopy:
        """Get book copy by accession number."""
        query = select(BookCopy).where(
            BookCopy.tenant_id == self.tenant_id,
            BookCopy.accession_number == accession_number,
        ).options(selectinload(BookCopy.book))
        result = await self.session.execute(query)
        copy = result.scalar_one_or_none()
        if not copy:
            raise ResourceNotFoundError("BookCopy", accession_number)
        return copy
    
    # ========== Borrowing ==========
    async def issue_book(
        self,
        accession_number: str,
        borrower_id: UUID,
        issued_by: UUID,
        due_days: int = 14,
    ) -> BorrowRecord:
        """Issue a book to a user."""
        copy = await self.get_copy_by_accession(accession_number)
        
        if copy.status != BookStatus.AVAILABLE:
            raise ValidationError(f"Book is not available (status: {copy.status.value})")
        
        book = await self.get_book(copy.book_id)
        
        # Create borrow record
        today = date.today()
        record = BorrowRecord(
            tenant_id=self.tenant_id,
            book_copy_id=copy.id,
            borrower_id=borrower_id,
            issued_by=issued_by,
            issue_date=today,
            due_date=today + timedelta(days=due_days),
            status=BorrowStatus.ACTIVE,
        )
        self.session.add(record)
        
        # Update copy status
        copy.status = BookStatus.BORROWED
        
        # Update book available count
        book.available_copies = max(0, book.available_copies - 1)
        
        await self.session.commit()
        await self.session.refresh(record)
        return record
    
    async def return_book(
        self,
        accession_number: str,
        returned_to: UUID,
        fine_paid: bool = True,
        notes: Optional[str] = None,
    ) -> BorrowRecord:
        """Return a borrowed book."""
        copy = await self.get_copy_by_accession(accession_number)
        
        # Find active borrow record
        query = select(BorrowRecord).where(
            BorrowRecord.tenant_id == self.tenant_id,
            BorrowRecord.book_copy_id == copy.id,
            BorrowRecord.status.in_([BorrowStatus.ACTIVE, BorrowStatus.OVERDUE]),
        )
        result = await self.session.execute(query)
        record = result.scalar_one_or_none()
        
        if not record:
            raise ValidationError("No active borrow record found for this copy")
        
        today = date.today()
        
        # Calculate fine if overdue
        if today > record.due_date:
            overdue_days = (today - record.due_date).days
            record.fine_amount = overdue_days * 10 * 100  # ₹10 per day in paise
        
        record.return_date = today
        record.returned_to = returned_to
        record.status = BorrowStatus.RETURNED
        record.fine_paid = fine_paid
        if notes:
            record.notes = notes
        
        # Update copy status
        copy.status = BookStatus.AVAILABLE
        
        # Update book available count
        book = await self.get_book(copy.book_id)
        book.available_copies += 1
        
        await self.session.commit()
        return record
    
    async def get_overdue_books(
        self,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[BorrowRecord], int]:
        """Get all overdue books."""
        today = date.today()
        
        query = select(BorrowRecord).where(
            BorrowRecord.tenant_id == self.tenant_id,
            BorrowRecord.status == BorrowStatus.ACTIVE,
            BorrowRecord.due_date < today,
        ).options(
            selectinload(BorrowRecord.book_copy).selectinload(BookCopy.book)
        )
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        skip = (page - 1) * size
        query = query.order_by(BorrowRecord.due_date).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def get_user_borrowed_books(self, user_id: UUID) -> List[BorrowRecord]:
        """Get books currently borrowed by a user."""
        query = select(BorrowRecord).where(
            BorrowRecord.tenant_id == self.tenant_id,
            BorrowRecord.borrower_id == user_id,
            BorrowRecord.status.in_([BorrowStatus.ACTIVE, BorrowStatus.OVERDUE]),
        ).options(
            selectinload(BorrowRecord.book_copy).selectinload(BookCopy.book)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_library_stats(self) -> dict:
        """Get library statistics."""
        today = date.today()
        
        # Total books
        books_count = await self.session.execute(
            select(func.count()).where(
                Book.tenant_id == self.tenant_id,
                Book.is_deleted == False,
            )
        )
        
        # Total copies
        copies_count = await self.session.execute(
            select(func.count()).where(
                BookCopy.tenant_id == self.tenant_id,
            )
        )
        
        # Available copies
        available_count = await self.session.execute(
            select(func.count()).where(
                BookCopy.tenant_id == self.tenant_id,
                BookCopy.status == BookStatus.AVAILABLE,
            )
        )
        
        # Borrowed copies
        borrowed_count = await self.session.execute(
            select(func.count()).where(
                BookCopy.tenant_id == self.tenant_id,
                BookCopy.status == BookStatus.BORROWED,
            )
        )
        
        # Overdue count
        overdue_count = await self.session.execute(
            select(func.count()).where(
                BorrowRecord.tenant_id == self.tenant_id,
                BorrowRecord.status == BorrowStatus.ACTIVE,
                BorrowRecord.due_date < today,
            )
        )
        
        # Issued today
        issued_today = await self.session.execute(
            select(func.count()).where(
                BorrowRecord.tenant_id == self.tenant_id,
                BorrowRecord.issue_date == today,
            )
        )
        
        return {
            "total_books": books_count.scalar() or 0,
            "total_copies": copies_count.scalar() or 0,
            "available_copies": available_count.scalar() or 0,
            "borrowed_copies": borrowed_count.scalar() or 0,
            "overdue_count": overdue_count.scalar() or 0,
            "books_issued_today": issued_today.scalar() or 0,
        }
