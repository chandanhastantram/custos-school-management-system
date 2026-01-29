"""
CUSTOS AI Background Tasks

Background task functions for long-running AI operations.
These are designed to be executed by RQ workers.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

# Note: These are standalone functions that will be pickled for RQ
# They must import everything they need inside the function

logger = logging.getLogger("custos.ai.tasks")


def process_question_generation_batch(
    tenant_id: str,
    job_id: str,
    teacher_id: str,
    topic_id: str,
    subject_id: str,
    class_id: str,
    difficulty: str,
    question_type: str,
    count: int,
    database_url: str,
) -> dict:
    """
    Background task for AI question generation.
    
    This runs in a separate worker process.
    Used for large batch generation (>20 questions).
    
    Args:
        tenant_id: Tenant UUID as string
        job_id: Pre-created job UUID as string
        teacher_id: Teacher UUID as string  
        topic_id: Topic UUID as string
        subject_id: Subject UUID as string
        class_id: Class UUID as string
        difficulty: Difficulty level
        question_type: Question type
        count: Number of questions to generate
        database_url: Database connection URL
    
    Returns:
        Result dict with status and created question IDs
    """
    import asyncio
    from uuid import UUID as UUIDType
    
    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select
        
        from app.ai.models import AIQuestionGenJob, AIJobStatus
        from app.ai.question_gen_service import AIQuestionGenService
        from app.ai.quota_manager import AIQuotaManager
        from app.ai.providers.openai import OpenAIProvider
        from app.academics.models.syllabus import SyllabusTopic
        
        # Create database connection
        engine = create_async_engine(database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Get the job
            job = await session.get(AIQuestionGenJob, UUIDType(job_id))
            if not job:
                return {"success": False, "error": "Job not found"}
            
            try:
                # Update status
                job.status = AIJobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)
                await session.commit()
                
                # Create service
                service = AIQuestionGenService(session, UUIDType(tenant_id))
                
                # Get topic
                topic = await service._get_topic_with_context(UUIDType(topic_id))
                if not topic:
                    raise ValueError("Topic not found")
                
                # Build input snapshot
                from app.ai.models import QuestionGenDifficulty, QuestionGenType
                diff = QuestionGenDifficulty(difficulty)
                q_type = QuestionGenType(question_type)
                
                input_snapshot = service._build_input_snapshot(topic, diff, q_type, count)
                job.input_snapshot = input_snapshot
                
                # Generate with AI
                ai_response = await service._generate_with_ai(input_snapshot)
                job.output_snapshot = ai_response
                job.tokens_used = ai_response.get("tokens_used", 0)
                
                # Create questions
                questions = await service._create_questions(
                    ai_response=ai_response,
                    topic=topic,
                    subject_id=UUIDType(subject_id),
                    teacher_id=UUIDType(teacher_id),
                    difficulty=diff,
                    question_type=q_type,
                )
                
                # Update job
                job.status = AIJobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.questions_created = len(questions)
                job.created_question_ids = [str(q.id) for q in questions]
                
                # Increment usage
                await service._increment_usage(len(questions))
                
                await session.commit()
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "questions_created": len(questions),
                    "question_ids": job.created_question_ids,
                }
                
            except Exception as e:
                logger.exception(f"Background job failed: {e}")
                job.status = AIJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": str(e),
                }
                
        await engine.dispose()
    
    # Run the async function
    return asyncio.run(_run())


def cleanup_old_ai_jobs(
    tenant_id: str,
    days_old: int,
    database_url: str,
) -> dict:
    """
    Clean up old AI job records.
    
    Background task to soft-delete completed/failed jobs older than X days.
    """
    import asyncio
    from datetime import timedelta
    from uuid import UUID as UUIDType
    
    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import update
        
        from app.ai.models import AIQuestionGenJob, AILessonPlanJob, AIJobStatus
        
        engine = create_async_engine(database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        async with async_session() as session:
            # Clean question gen jobs
            qgen_result = await session.execute(
                update(AIQuestionGenJob)
                .where(
                    AIQuestionGenJob.tenant_id == UUIDType(tenant_id),
                    AIQuestionGenJob.status.in_([AIJobStatus.COMPLETED, AIJobStatus.FAILED]),
                    AIQuestionGenJob.completed_at < cutoff,
                    AIQuestionGenJob.is_deleted == False,
                )
                .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
            )
            
            await session.commit()
            
            return {
                "deleted_count": qgen_result.rowcount,
            }
        
        await engine.dispose()
    
    return asyncio.run(_run())
