"""
CUSTOS Feedback & Surveys Router

API endpoints for survey management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.users.rbac import Permission
from app.feedback.models import SurveyType, SurveyStatus
from app.feedback.schemas import (
    SurveyCreate, SurveyUpdate, SurveyResponse, SurveyWithQuestions,
    SurveyListResponse, SurveyQuestionCreate, SurveyQuestionResponse,
    SubmitSurveyRequest, SurveySubmissionResponse, SurveyResultsSummary,
    StudentSurveyList, SurveyTemplateResponse
)
from app.feedback.service import FeedbackService


router = APIRouter(tags=["Feedback & Surveys"])


def get_feedback_service(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
) -> FeedbackService:
    """Get feedback service instance."""
    return FeedbackService(db, user.tenant_id)


# ============================================
# Survey Management (Admin)
# ============================================

@router.get("/surveys", response_model=SurveyListResponse)
async def list_surveys(
    survey_type: Optional[SurveyType] = None,
    status: Optional[SurveyStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_VIEW])),
):
    """List all surveys (admin)."""
    surveys, total = await service.list_surveys(
        survey_type=survey_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return SurveyListResponse(
        surveys=[SurveyResponse.model_validate(s) for s in surveys],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/surveys", response_model=SurveyWithQuestions, status_code=201)
async def create_survey(
    data: SurveyCreate,
    service: FeedbackService = Depends(get_feedback_service),
    user = Depends(get_current_user),
    _: None = Depends(require_permissions([Permission.SURVEY_CREATE])),
):
    """Create a new survey."""
    survey = await service.create_survey(data, user.user_id)
    return SurveyWithQuestions.model_validate(survey)


@router.get("/surveys/{survey_id}", response_model=SurveyWithQuestions)
async def get_survey(
    survey_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_VIEW])),
):
    """Get survey details."""
    survey = await service.get_survey(survey_id)
    return SurveyWithQuestions.model_validate(survey)


@router.put("/surveys/{survey_id}", response_model=SurveyResponse)
async def update_survey(
    survey_id: UUID,
    data: SurveyUpdate,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_UPDATE])),
):
    """Update a survey."""
    survey = await service.update_survey(survey_id, data)
    return SurveyResponse.model_validate(survey)


@router.delete("/surveys/{survey_id}", status_code=204)
async def delete_survey(
    survey_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_DELETE])),
):
    """Delete a survey."""
    await service.delete_survey(survey_id)


@router.post("/surveys/{survey_id}/publish", response_model=SurveyResponse)
async def publish_survey(
    survey_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_UPDATE])),
):
    """Publish a draft survey."""
    survey = await service.publish_survey(survey_id)
    return SurveyResponse.model_validate(survey)


@router.post("/surveys/{survey_id}/close", response_model=SurveyResponse)
async def close_survey(
    survey_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_UPDATE])),
):
    """Close an active survey."""
    survey = await service.close_survey(survey_id)
    return SurveyResponse.model_validate(survey)


# ============================================
# Question Management
# ============================================

@router.post("/surveys/{survey_id}/questions", response_model=SurveyQuestionResponse, status_code=201)
async def add_question(
    survey_id: UUID,
    data: SurveyQuestionCreate,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_UPDATE])),
):
    """Add a question to a survey."""
    question = await service.add_question(survey_id, data)
    return SurveyQuestionResponse.model_validate(question)


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_UPDATE])),
):
    """Delete a question from a survey."""
    await service.delete_question(question_id)


# ============================================
# Student Survey Submission
# ============================================

@router.get("/my-surveys", response_model=StudentSurveyList)
async def get_my_surveys(
    service: FeedbackService = Depends(get_feedback_service),
    user = Depends(get_current_user),
):
    """Get surveys available for the current student."""
    # Get student's class from profile
    class_id = None
    if hasattr(user, 'student_profile') and user.student_profile:
        class_id = user.student_profile.class_id
    
    return await service.get_student_surveys(user.user_id, class_id)


@router.get("/surveys/{survey_id}/for-submission", response_model=SurveyWithQuestions)
async def get_survey_for_submission(
    survey_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    user = Depends(get_current_user),
):
    """Get survey with questions for student submission."""
    survey = await service.get_survey(survey_id)
    return SurveyWithQuestions.model_validate(survey)


@router.post("/surveys/{survey_id}/submit", response_model=SurveySubmissionResponse)
async def submit_survey(
    survey_id: UUID,
    data: SubmitSurveyRequest,
    request: Request,
    service: FeedbackService = Depends(get_feedback_service),
    user = Depends(get_current_user),
):
    """Submit a survey response."""
    ip_address = request.client.host if request.client else None
    response = await service.submit_survey(
        survey_id, user.user_id, data, ip_address
    )
    return SurveySubmissionResponse.model_validate(response)


# ============================================
# Results & Analytics
# ============================================

@router.get("/surveys/{survey_id}/results", response_model=SurveyResultsSummary)
async def get_survey_results(
    survey_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_RESULTS_VIEW])),
):
    """Get aggregated survey results (admin/faculty)."""
    return await service.get_survey_results(survey_id)


# ============================================
# Templates
# ============================================

@router.get("/templates", response_model=list[SurveyTemplateResponse])
async def list_templates(
    survey_type: Optional[SurveyType] = None,
    service: FeedbackService = Depends(get_feedback_service),
    _: None = Depends(require_permissions([Permission.SURVEY_CREATE])),
):
    """List available survey templates."""
    templates = await service.list_templates(survey_type)
    return [SurveyTemplateResponse.model_validate(t) for t in templates]


@router.post("/templates/{template_id}/create-survey", response_model=SurveyWithQuestions, status_code=201)
async def create_survey_from_template(
    template_id: UUID,
    data: SurveyCreate,
    service: FeedbackService = Depends(get_feedback_service),
    user = Depends(get_current_user),
    _: None = Depends(require_permissions([Permission.SURVEY_CREATE])),
):
    """Create a survey from a template."""
    survey = await service.create_survey_from_template(template_id, data, user.user_id)
    return SurveyWithQuestions.model_validate(survey)
