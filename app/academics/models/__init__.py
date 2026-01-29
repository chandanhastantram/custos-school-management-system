"""
CUSTOS Academic Models Init
"""

from app.academics.models.structure import AcademicYear, Class, Section
from app.academics.models.curriculum import Subject, Syllabus, Topic, Lesson
from app.academics.models.teaching_assignments import TeachingAssignment
from app.academics.models.lesson_plans import LessonPlan, LessonPlanUnit, TeachingProgress

__all__ = [
    "AcademicYear",
    "Class",
    "Section",
    "Subject",
    "Syllabus",
    "Topic",
    "Lesson",
    "TeachingAssignment",
    "LessonPlan",
    "LessonPlanUnit",
    "TeachingProgress",
]
