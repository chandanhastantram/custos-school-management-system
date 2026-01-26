"""
CUSTOS AI Models

Models for AI sessions and usage tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime,
    ForeignKey, Enum as SQLEnum, JSON, Float,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBaseModel

if TYPE_CHECKING:
    from app.models.user import User


class AIFeature(str, Enum):
    LESSON_PLAN = "lesson_plan"
    QUESTION_GENERATION = "question_generation"
    WORKSHEET_GENERATION = "worksheet_generation"
    DOUBT_SOLVER = "doubt_solver"
    CONTENT_SUMMARY = "content_summary"


class AISession(TenantBaseModel):
    """AI interaction session."""
    __tablename__ = "ai_sessions"
    
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    feature: Mapped[AIFeature] = mapped_column(SQLEnum(AIFeature), nullable=False)
    
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    user: Mapped["User"] = relationship("User", lazy="selectin")


class AIUsage(TenantBaseModel):
    """Monthly AI usage tracking per tenant."""
    __tablename__ = "ai_usages"
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    
    tokens_by_feature: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    limit_tokens: Mapped[int] = mapped_column(Integer, default=10000)
    is_limit_reached: Mapped[bool] = mapped_column(Boolean, default=False)
