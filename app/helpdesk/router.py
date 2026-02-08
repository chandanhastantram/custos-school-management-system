"""
CUSTOS Helpdesk Router

API endpoints for support tickets, applications, and student services.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id
from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import UserResponse

from app.helpdesk.service import HelpdeskService
from app.helpdesk.schemas import (
    # Ticket schemas
    TicketCreate, TicketUpdate, TicketResponse, TicketListResponse,
    TicketCommentCreate, TicketCommentResponse,
    TicketAssign, TicketResolve, TicketSatisfaction,
    # Application schemas
    ApplicationResponse,
    # Transcript schemas
    TranscriptApplicationCreate, TranscriptApplicationResponse,
    # Grace mark schemas
    GraceMarkApplicationCreate, GraceMarkApplicationResponse, GraceMarkReview,
    # Redistribution schemas
    GraceRedistributionCreate, GraceRedistributionResponse,
    # FAQ schemas
    FAQCreate, FAQUpdate, FAQResponse, FAQFeedback,
    # Statistics
    TicketStatistics, HelpdeskCategory,
)


router = APIRouter(tags=["Helpdesk"])


def get_helpdesk_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> HelpdeskService:
    """Get helpdesk service instance."""
    return HelpdeskService(db, tenant_id)


# ============================================
# Ticket Endpoints
# ============================================

@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get list of helpdesk categories."""
    return [c.value for c in HelpdeskCategory]


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new support ticket."""
    ticket = await service.create_ticket(data, current_user.id)
    return TicketResponse.model_validate(ticket)


@router.get("/tickets", response_model=TicketListResponse)
async def list_tickets(
    category: Optional[str] = Query(None),
    ticket_status: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """List tickets. Users see their own, staff sees all."""
    # Check if staff
    is_staff = current_user.role in ["admin", "principal", "sub_admin", "teacher"]
    user_id = None if is_staff else current_user.id
    
    tickets, total = await service.list_tickets(
        user_id=user_id,
        category=category,
        status=ticket_status,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )
    
    return TicketListResponse(
        items=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get ticket details."""
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check access
    is_staff = current_user.role in ["admin", "principal", "sub_admin", "teacher"]
    if not is_staff and ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return TicketResponse.model_validate(ticket)


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update a ticket."""
    ticket = await service.update_ticket(ticket_id, data, current_user.id)
    return TicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: UUID,
    data: TicketAssign,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Assign ticket to staff member."""
    ticket = await service.assign_ticket(ticket_id, data.assigned_to, current_user.id)
    return TicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
async def resolve_ticket(
    ticket_id: UUID,
    data: TicketResolve,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Resolve a ticket."""
    ticket = await service.resolve_ticket(
        ticket_id, data.resolution_notes, current_user.id
    )
    return TicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: UUID,
    data: TicketCommentCreate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Add comment to ticket."""
    comment = await service.add_comment(ticket_id, data, current_user.id)
    return TicketCommentResponse.model_validate(comment)


@router.post("/tickets/{ticket_id}/satisfaction", response_model=TicketResponse)
async def submit_satisfaction(
    ticket_id: UUID,
    data: TicketSatisfaction,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Submit satisfaction rating for resolved ticket."""
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only ticket creator can rate")
    
    ticket.satisfaction_rating = data.rating
    ticket.satisfaction_feedback = data.feedback
    
    await service.db.commit()
    await service.db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


# ============================================
# Transcript Application Endpoints
# ============================================

@router.post("/applications/transcript", response_model=TranscriptApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_transcript(
    data: TranscriptApplicationCreate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Apply for academic transcript."""
    application = await service.apply_for_transcript(data, current_user.id)
    return TranscriptApplicationResponse.model_validate(application)


@router.get("/applications/transcript", response_model=List[TranscriptApplicationResponse])
async def get_transcript_applications(
    app_status: Optional[str] = Query(None, alias="status"),
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get transcript applications."""
    is_staff = current_user.role in ["admin", "principal", "sub_admin"]
    student_id = None if is_staff else current_user.id
    
    applications = await service.get_transcript_applications(
        student_id=student_id,
        status=app_status,
    )
    return [TranscriptApplicationResponse.model_validate(a) for a in applications]


# ============================================
# Grace Mark Application Endpoints
# ============================================

@router.post("/applications/grace-mark", response_model=GraceMarkApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_grace_marks(
    data: GraceMarkApplicationCreate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Apply for grace marks."""
    application = await service.apply_for_grace_marks(data, current_user.id)
    return GraceMarkApplicationResponse.model_validate(application)


@router.get("/applications/grace-mark", response_model=List[GraceMarkApplicationResponse])
async def get_grace_mark_applications(
    exam_id: Optional[UUID] = Query(None),
    app_status: Optional[str] = Query(None, alias="status"),
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get grace mark applications."""
    is_staff = current_user.role in ["admin", "principal", "sub_admin", "teacher"]
    student_id = None if is_staff else current_user.id
    
    applications = await service.get_grace_mark_applications(
        student_id=student_id,
        exam_id=exam_id,
        status=app_status,
    )
    return [GraceMarkApplicationResponse.model_validate(a) for a in applications]


@router.put("/applications/grace-mark/{application_id}/review", response_model=GraceMarkApplicationResponse)
async def review_grace_mark(
    application_id: UUID,
    data: GraceMarkReview,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Review grace mark application."""
    application = await service.review_grace_mark(
        application_id,
        data.approved_marks,
        data.status,
        data.verification_remarks,
        current_user.id,
    )
    return GraceMarkApplicationResponse.model_validate(application)


# ============================================
# Grace Mark Redistribution Endpoints
# ============================================

@router.post("/applications/grace-redistribution", response_model=GraceRedistributionResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_redistribution(
    data: GraceRedistributionCreate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Apply for grace mark redistribution."""
    application = await service.apply_for_redistribution(data, current_user.id)
    return GraceRedistributionResponse.model_validate(application)


# ============================================
# FAQ Endpoints
# ============================================

@router.get("/faqs", response_model=List[FAQResponse])
async def list_faqs(
    category: Optional[str] = Query(None),
    service: HelpdeskService = Depends(get_helpdesk_service),
):
    """List FAQs (public endpoint)."""
    faqs = await service.list_faqs(category=category, published_only=True)
    return [FAQResponse.model_validate(f) for f in faqs]


@router.post("/faqs", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    data: FAQCreate,
    service: HelpdeskService = Depends(get_helpdesk_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Create a new FAQ."""
    faq = await service.create_faq(data)
    return FAQResponse.model_validate(faq)


@router.post("/faqs/{faq_id}/feedback", response_model=FAQResponse)
async def submit_faq_feedback(
    faq_id: UUID,
    data: FAQFeedback,
    service: HelpdeskService = Depends(get_helpdesk_service),
):
    """Submit FAQ feedback (was it helpful?)."""
    faq = await service.record_faq_feedback(faq_id, data.helpful)
    return FAQResponse.model_validate(faq)
