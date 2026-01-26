"""
CUSTOS Notification Schemas

Notification request/response schemas.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.audit import NotificationType


class NotificationCreate(BaseModel):
    """Create notification."""
    type: NotificationType = NotificationType.GENERAL
    title: str = Field(..., min_length=1, max_length=200)
    message: str
    data: Optional[dict] = None
    action_url: Optional[str] = None


class NotificationResponse(BaseModel):
    """Notification response."""
    id: UUID
    type: str
    title: str
    message: str
    action_url: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
