"""
CUSTOS Feedback & Surveys Service

Business logic for survey management.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.feedback.models import (
    Survey, SurveyQuestion, SurveyResponse, SurveyAnswer,
    SurveyTemplate, SurveyType, SurveyStatus, ResponseStatus, QuestionType
)
from app.feedback.schemas import (
    SurveyCreate, SurveyUpdate, SurveyQuestionCreate,
    SubmitSurveyRequest, SurveyResultsSummary, QuestionStats,
    StudentSurveyItem, StudentSurveyList
)
from app.core.exceptions import NotFoundError, BadRequestError, ForbiddenError


class FeedbackService:
    """Service for managing surveys and feedback."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Survey CRUD
    # ============================================
    
    async def create_survey(
        self,
        data: SurveyCreate,
        created_by: UUID,
    ) -> Survey:
        """Create a new survey."""
        survey = Survey(
            tenant_id=self.tenant_id,
            title=data.title,
            description=data.description,
            survey_type=data.survey_type,
            start_date=data.start_date,
            end_date=data.end_date,
            is_anonymous=data.is_anonymous,
            is_mandatory=data.is_mandatory,
            allow_multiple_submissions=data.allow_multiple_submissions,
            show_results_to_students=data.show_results_to_students,
            academic_year_id=data.academic_year_id,
            class_id=data.class_id,
            section_id=data.section_id,
            subject_id=data.subject_id,
            faculty_id=data.faculty_id,
            created_by=created_by,
            status=SurveyStatus.DRAFT,
        )
        
        self.session.add(survey)
        await self.session.flush()
        
        # Add questions if provided
        if data.questions:
            for idx, q_data in enumerate(data.questions):
                question = SurveyQuestion(
                    tenant_id=self.tenant_id,
                    survey_id=survey.id,
                    question_text=q_data.question_text,
                    question_type=q_data.question_type,
                    options=[opt.model_dump() for opt in q_data.options] if q_data.options else None,
                    min_value=q_data.min_value,
                    max_value=q_data.max_value,
                    is_required=q_data.is_required,
                    display_order=q_data.display_order or idx,
                    help_text=q_data.help_text,
                    category=q_data.category,
                )
                self.session.add(question)
        
        await self.session.commit()
        await self.session.refresh(survey)
        return survey
    
    async def get_survey(self, survey_id: UUID) -> Survey:
        """Get survey by ID."""
        query = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(
                and_(
                    Survey.id == survey_id,
                    Survey.tenant_id == self.tenant_id,
                )
            )
        )
        result = await self.session.execute(query)
        survey = result.scalar_one_or_none()
        
        if not survey:
            raise NotFoundError("Survey not found")
        
        return survey
    
    async def list_surveys(
        self,
        survey_type: Optional[SurveyType] = None,
        status: Optional[SurveyStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Survey], int]:
        """List surveys with filters."""
        query = select(Survey).where(Survey.tenant_id == self.tenant_id)
        
        if survey_type:
            query = query.where(Survey.survey_type == survey_type)
        if status:
            query = query.where(Survey.status == status)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Paginate
        query = query.order_by(Survey.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        surveys = list(result.scalars().all())
        
        return surveys, total
    
    async def update_survey(
        self,
        survey_id: UUID,
        data: SurveyUpdate,
    ) -> Survey:
        """Update a survey."""
        survey = await self.get_survey(survey_id)
        
        # Don't allow updates to active/closed surveys
        if survey.status in (SurveyStatus.ACTIVE, SurveyStatus.CLOSED):
            raise BadRequestError("Cannot update active or closed survey")
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(survey, field, value)
        
        await self.session.commit()
        await self.session.refresh(survey)
        return survey
    
    async def delete_survey(self, survey_id: UUID) -> None:
        """Delete a survey."""
        survey = await self.get_survey(survey_id)
        
        if survey.total_responses > 0:
            raise BadRequestError("Cannot delete survey with responses")
        
        await self.session.delete(survey)
        await self.session.commit()
    
    async def publish_survey(self, survey_id: UUID) -> Survey:
        """Publish a draft survey."""
        survey = await self.get_survey(survey_id)
        
        if survey.status != SurveyStatus.DRAFT:
            raise BadRequestError("Only draft surveys can be published")
        
        if not survey.questions:
            raise BadRequestError("Survey must have at least one question")
        
        now = datetime.now(timezone.utc)
        
        if survey.start_date <= now <= survey.end_date:
            survey.status = SurveyStatus.ACTIVE
        elif survey.start_date > now:
            survey.status = SurveyStatus.SCHEDULED
        else:
            raise BadRequestError("Survey dates have passed")
        
        survey.published_at = now
        await self.session.commit()
        await self.session.refresh(survey)
        return survey
    
    async def close_survey(self, survey_id: UUID) -> Survey:
        """Close an active survey."""
        survey = await self.get_survey(survey_id)
        
        if survey.status != SurveyStatus.ACTIVE:
            raise BadRequestError("Only active surveys can be closed")
        
        survey.status = SurveyStatus.CLOSED
        survey.closed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(survey)
        return survey
    
    # ============================================
    # Question Management
    # ============================================
    
    async def add_question(
        self,
        survey_id: UUID,
        data: SurveyQuestionCreate,
    ) -> SurveyQuestion:
        """Add a question to a survey."""
        survey = await self.get_survey(survey_id)
        
        if survey.status != SurveyStatus.DRAFT:
            raise BadRequestError("Can only add questions to draft surveys")
        
        question = SurveyQuestion(
            tenant_id=self.tenant_id,
            survey_id=survey_id,
            question_text=data.question_text,
            question_type=data.question_type,
            options=[opt.model_dump() for opt in data.options] if data.options else None,
            min_value=data.min_value,
            max_value=data.max_value,
            is_required=data.is_required,
            display_order=data.display_order,
            help_text=data.help_text,
            category=data.category,
        )
        
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def delete_question(self, question_id: UUID) -> None:
        """Delete a question from a survey."""
        query = select(SurveyQuestion).where(
            and_(
                SurveyQuestion.id == question_id,
                SurveyQuestion.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(query)
        question = result.scalar_one_or_none()
        
        if not question:
            raise NotFoundError("Question not found")
        
        # Check survey status
        survey = await self.get_survey(question.survey_id)
        if survey.status != SurveyStatus.DRAFT:
            raise BadRequestError("Can only delete questions from draft surveys")
        
        await self.session.delete(question)
        await self.session.commit()
    
    # ============================================
    # Student Response Submission
    # ============================================
    
    async def get_student_surveys(
        self,
        student_id: UUID,
        class_id: Optional[UUID] = None,
    ) -> StudentSurveyList:
        """Get surveys available for a student."""
        now = datetime.now(timezone.utc)
        
        # Base query for active surveys
        query = select(Survey).where(
            and_(
                Survey.tenant_id == self.tenant_id,
                Survey.status == SurveyStatus.ACTIVE,
                Survey.start_date <= now,
                Survey.end_date >= now,
            )
        )
        
        if class_id:
            query = query.where(
                or_(
                    Survey.class_id == class_id,
                    Survey.class_id.is_(None),
                )
            )
        
        result = await self.session.execute(query)
        surveys = list(result.scalars().all())
        
        # Check which ones the student has submitted
        response_query = select(SurveyResponse.survey_id, SurveyResponse.submitted_at).where(
            and_(
                SurveyResponse.student_id == student_id,
                SurveyResponse.tenant_id == self.tenant_id,
                SurveyResponse.status == ResponseStatus.SUBMITTED,
            )
        )
        response_result = await self.session.execute(response_query)
        submitted = {r.survey_id: r.submitted_at for r in response_result}
        
        pending = []
        completed = []
        
        for survey in surveys:
            item = StudentSurveyItem(
                id=survey.id,
                title=survey.title,
                description=survey.description,
                survey_type=survey.survey_type,
                start_date=survey.start_date,
                end_date=survey.end_date,
                is_mandatory=survey.is_mandatory,
                is_submitted=survey.id in submitted,
                submitted_at=submitted.get(survey.id),
            )
            
            if survey.id in submitted:
                completed.append(item)
            else:
                pending.append(item)
        
        return StudentSurveyList(pending=pending, completed=completed)
    
    async def submit_survey(
        self,
        survey_id: UUID,
        student_id: UUID,
        data: SubmitSurveyRequest,
        ip_address: Optional[str] = None,
    ) -> SurveyResponse:
        """Submit a survey response."""
        survey = await self.get_survey(survey_id)
        
        # Validate survey is active
        if survey.status != SurveyStatus.ACTIVE:
            raise BadRequestError("Survey is not active")
        
        now = datetime.now(timezone.utc)
        if not (survey.start_date <= now <= survey.end_date):
            raise BadRequestError("Survey is not within submission period")
        
        # Check for existing response
        existing_query = select(SurveyResponse).where(
            and_(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.student_id == student_id,
                SurveyResponse.tenant_id == self.tenant_id,
            )
        )
        existing = (await self.session.execute(existing_query)).scalar_one_or_none()
        
        if existing and existing.status == ResponseStatus.SUBMITTED:
            if not survey.allow_multiple_submissions:
                raise BadRequestError("You have already submitted this survey")
        
        # Create response
        response = existing or SurveyResponse(
            tenant_id=self.tenant_id,
            survey_id=survey_id,
            student_id=student_id,
            ip_address=ip_address,
        )
        
        if not existing:
            self.session.add(response)
            await self.session.flush()
        
        # Validate and save answers
        question_ids = {q.id for q in survey.questions}
        required_ids = {q.id for q in survey.questions if q.is_required}
        answered_ids = set()
        
        for answer_data in data.answers:
            if answer_data.question_id not in question_ids:
                raise BadRequestError(f"Invalid question ID: {answer_data.question_id}")
            
            answered_ids.add(answer_data.question_id)
            
            # Check if answer already exists
            existing_answer_query = select(SurveyAnswer).where(
                and_(
                    SurveyAnswer.response_id == response.id,
                    SurveyAnswer.question_id == answer_data.question_id,
                )
            )
            existing_answer = (await self.session.execute(existing_answer_query)).scalar_one_or_none()
            
            if existing_answer:
                # Update existing
                existing_answer.rating_value = answer_data.rating_value
                existing_answer.text_value = answer_data.text_value
                existing_answer.selected_option = answer_data.selected_option
                existing_answer.boolean_value = answer_data.boolean_value
                existing_answer.numeric_value = answer_data.numeric_value
            else:
                # Create new
                answer = SurveyAnswer(
                    tenant_id=self.tenant_id,
                    response_id=response.id,
                    question_id=answer_data.question_id,
                    rating_value=answer_data.rating_value,
                    text_value=answer_data.text_value,
                    selected_option=answer_data.selected_option,
                    boolean_value=answer_data.boolean_value,
                    numeric_value=answer_data.numeric_value,
                )
                self.session.add(answer)
        
        # Check required questions
        missing = required_ids - answered_ids
        if missing:
            raise BadRequestError(f"Missing required questions: {len(missing)}")
        
        # Mark as submitted
        response.status = ResponseStatus.SUBMITTED
        response.submitted_at = now
        
        # Update survey response count
        survey.total_responses += 1
        
        await self.session.commit()
        await self.session.refresh(response)
        return response
    
    # ============================================
    # Results & Analytics
    # ============================================
    
    async def get_survey_results(self, survey_id: UUID) -> SurveyResultsSummary:
        """Get aggregated survey results."""
        survey = await self.get_survey(survey_id)
        
        # Get all submitted responses
        response_query = select(SurveyResponse).where(
            and_(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.status == ResponseStatus.SUBMITTED,
            )
        ).options(selectinload(SurveyResponse.answers))
        
        responses = (await self.session.execute(response_query)).scalars().all()
        
        # Calculate stats per question
        question_stats = []
        overall_ratings = []
        category_ratings: dict = {}
        
        for question in survey.questions:
            answers = []
            for response in responses:
                for answer in response.answers:
                    if answer.question_id == question.id:
                        answers.append(answer)
            
            stats = QuestionStats(
                question_id=question.id,
                question_text=question.question_text,
                question_type=question.question_type,
                total_responses=len(answers),
            )
            
            if question.question_type in (QuestionType.RATING, QuestionType.SCALE, QuestionType.LIKERT):
                ratings = [a.rating_value or a.numeric_value for a in answers if a.rating_value or a.numeric_value]
                if ratings:
                    stats.average_rating = sum(ratings) / len(ratings)
                    stats.min_rating = int(min(ratings))
                    stats.max_rating = int(max(ratings))
                    stats.rating_distribution = {}
                    for r in ratings:
                        key = str(int(r))
                        stats.rating_distribution[key] = stats.rating_distribution.get(key, 0) + 1
                    
                    overall_ratings.extend(ratings)
                    
                    if question.category:
                        if question.category not in category_ratings:
                            category_ratings[question.category] = []
                        category_ratings[question.category].extend(ratings)
            
            elif question.question_type == QuestionType.MCQ:
                stats.option_counts = {}
                for a in answers:
                    if a.selected_option:
                        stats.option_counts[a.selected_option] = stats.option_counts.get(a.selected_option, 0) + 1
            
            elif question.question_type == QuestionType.YES_NO:
                stats.yes_count = sum(1 for a in answers if a.boolean_value is True)
                stats.no_count = sum(1 for a in answers if a.boolean_value is False)
            
            question_stats.append(stats)
        
        # Calculate category averages
        category_averages = None
        if category_ratings:
            category_averages = {
                cat: sum(ratings) / len(ratings)
                for cat, ratings in category_ratings.items()
            }
        
        return SurveyResultsSummary(
            survey_id=survey.id,
            survey_title=survey.title,
            survey_type=survey.survey_type,
            total_responses=len(responses),
            target_respondents=survey.target_respondents,
            response_rate=(len(responses) / survey.target_respondents * 100) if survey.target_respondents > 0 else 0,
            average_overall_rating=sum(overall_ratings) / len(overall_ratings) if overall_ratings else None,
            question_stats=question_stats,
            category_averages=category_averages,
        )
    
    # ============================================
    # Templates
    # ============================================
    
    async def list_templates(
        self,
        survey_type: Optional[SurveyType] = None,
    ) -> List[SurveyTemplate]:
        """List available survey templates."""
        query = select(SurveyTemplate).where(
            and_(
                SurveyTemplate.tenant_id == self.tenant_id,
                SurveyTemplate.is_active == True,
            )
        )
        
        if survey_type:
            query = query.where(SurveyTemplate.survey_type == survey_type)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_survey_from_template(
        self,
        template_id: UUID,
        data: SurveyCreate,
        created_by: UUID,
    ) -> Survey:
        """Create a survey from a template."""
        # Get template
        query = select(SurveyTemplate).where(
            and_(
                SurveyTemplate.id == template_id,
                SurveyTemplate.tenant_id == self.tenant_id,
            )
        )
        template = (await self.session.execute(query)).scalar_one_or_none()
        
        if not template:
            raise NotFoundError("Template not found")
        
        # Create survey
        survey = await self.create_survey(data, created_by)
        
        # Add template questions
        for idx, q_data in enumerate(template.questions):
            question = SurveyQuestion(
                tenant_id=self.tenant_id,
                survey_id=survey.id,
                question_text=q_data.get("question_text", ""),
                question_type=q_data.get("question_type", QuestionType.RATING),
                options=q_data.get("options"),
                is_required=q_data.get("is_required", True),
                display_order=idx,
                help_text=q_data.get("help_text"),
                category=q_data.get("category"),
            )
            self.session.add(question)
        
        await self.session.commit()
        await self.session.refresh(survey)
        return survey
