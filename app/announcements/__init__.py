"""
CUSTOS Announcements Module

School announcements, posts, and communication.
"""

from app.announcements.models import Post, PostRead, PostType, PostPriority, TargetAudience
from app.announcements.service import AnnouncementsService
from app.announcements.router import router as announcements_router

__all__ = [
    "Post",
    "PostRead",
    "PostType", 
    "PostPriority",
    "TargetAudience",
    "AnnouncementsService",
    "announcements_router",
]
