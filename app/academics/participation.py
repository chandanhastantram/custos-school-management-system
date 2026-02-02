"""
CUSTOS Participation Status

Distinguishes absence from poor performance.

CORE PRINCIPLE:
    Absence ≠ Poor Performance
    
    - Excused absence: Medical, approved leave → NOT counted against student
    - Unexcused absence: Skipped without approval → COUNTS as zero
    - Participation: Actually attempted → Normal evaluation

USAGE:

    from app.academics.participation import (
        ParticipationStatus,
        should_include_in_mastery,
        get_mastery_contribution,
    )
    
    # When calculating mastery
    for result in test_results:
        if should_include_in_mastery(result.participation_status):
            # Include in calculation
            include_score(result.score)
        else:
            # Skip from denominator entirely
            pass
"""

from enum import Enum
from typing import Optional, List, Tuple
from dataclasses import dataclass


class ParticipationStatus(str, Enum):
    """
    Participation status for any academic/attendance event.
    
    This is ORTHOGONAL to marks, mastery, or scores.
    """
    PARTICIPATED = "participated"          # Attempted / attended
    EXCUSED_ABSENT = "excused_absent"      # Valid absence (medical, approved leave)
    UNEXCUSED_ABSENT = "unexcused_absent"  # Skipped without approval
    NOT_SCHEDULED = "not_scheduled"        # Not applicable (no class / not enrolled yet)


class AbsenceReason(str, Enum):
    """Reasons for excused absence."""
    MEDICAL = "medical"
    FAMILY_EMERGENCY = "family_emergency"
    APPROVED_LEAVE = "approved_leave"
    SCHOOL_EVENT = "school_event"          # Student was at another school event
    EXAM_CONFLICT = "exam_conflict"
    TRANSPORT_ISSUE = "transport_issue"    # School transport failure
    WEATHER = "weather"                    # Weather/natural event
    OTHER = "other"


@dataclass
class ParticipationRecord:
    """Standard participation record for any activity."""
    status: ParticipationStatus
    reason: Optional[AbsenceReason] = None
    reason_detail: Optional[str] = None
    reference_document: Optional[str] = None  # Leave application, medical certificate
    marked_by_id: Optional[str] = None
    marked_at: Optional[str] = None


# ============================================
# Mastery Calculation Rules
# ============================================

def should_include_in_mastery(status: ParticipationStatus) -> bool:
    """
    Determine if this participation status should be included in mastery calculation.
    
    Rules:
    - PARTICIPATED: Yes, include actual score
    - UNEXCUSED_ABSENT: Yes, include as zero
    - EXCUSED_ABSENT: NO, exclude from denominator
    - NOT_SCHEDULED: NO, exclude from denominator
    """
    return status in {
        ParticipationStatus.PARTICIPATED,
        ParticipationStatus.UNEXCUSED_ABSENT,
    }


def get_mastery_contribution(
    status: ParticipationStatus,
    actual_score: Optional[float],
    max_score: float,
) -> Tuple[Optional[float], bool]:
    """
    Get score contribution for mastery calculation.
    
    Returns:
        (score_to_use, should_include_in_denominator)
    
    Rules:
    - PARTICIPATED: (actual_score, True)
    - UNEXCUSED_ABSENT: (0, True) - counts as zero
    - EXCUSED_ABSENT: (None, False) - excluded entirely
    - NOT_SCHEDULED: (None, False) - excluded entirely
    """
    if status == ParticipationStatus.PARTICIPATED:
        return (actual_score or 0, True)
    
    if status == ParticipationStatus.UNEXCUSED_ABSENT:
        return (0, True)
    
    # EXCUSED_ABSENT or NOT_SCHEDULED
    return (None, False)


def calculate_fair_mastery(
    results: List[Tuple[ParticipationStatus, Optional[float], float]],
) -> Optional[float]:
    """
    Calculate fair mastery from a list of (status, score, max_score) tuples.
    
    Excludes excused absences from denominator.
    Includes unexcused absences as zero.
    
    Returns None if no valid data points.
    """
    total_score = 0.0
    total_possible = 0.0
    
    for status, score, max_score in results:
        contribution, include = get_mastery_contribution(status, score, max_score)
        
        if include:
            total_score += contribution or 0
            total_possible += max_score
    
    if total_possible == 0:
        return None  # No valid data
    
    return (total_score / total_possible) * 100


# ============================================
# Analytics Impact Rules
# ============================================

def get_activity_score_penalty(
    excused_count: int,
    unexcused_count: int,
    total_events: int,
) -> float:
    """
    Calculate activity score considering only unexcused absences.
    
    Excused absences do NOT penalize activity score.
    Only unexcused absences reduce activity score.
    
    Returns penalty factor (0.0 to 1.0, where 1.0 = no penalty)
    """
    if total_events == 0:
        return 1.0
    
    # Only unexcused absences count against activity
    participated = total_events - excused_count - unexcused_count
    effective_total = total_events - excused_count  # Exclude excused from denominator
    
    if effective_total == 0:
        return 1.0
    
    return participated / effective_total


def categorize_absence_pattern(
    excused_count: int,
    unexcused_count: int,
    total_events: int,
) -> dict:
    """
    Categorize absence pattern for AI/insights.
    
    Returns structured data for responsible AI inference.
    """
    if total_events == 0:
        return {
            "pattern": "no_data",
            "concern_level": "none",
            "inference_safe": False,
        }
    
    excused_rate = excused_count / total_events
    unexcused_rate = unexcused_count / total_events
    
    # High excused absence - suggest support, NOT remediation
    if excused_rate > 0.3:
        return {
            "pattern": "high_excused_absence",
            "concern_level": "support_needed",
            "inference_safe": False,  # Do NOT infer academic weakness
            "note": "Reduced participation appears linked to excused absences rather than learning difficulty.",
        }
    
    # High unexcused absence - engagement concern
    if unexcused_rate > 0.2:
        return {
            "pattern": "high_unexcused_absence",
            "concern_level": "engagement_concern",
            "inference_safe": True,  # Can infer engagement issue
            "note": "Student may benefit from engagement support.",
        }
    
    return {
        "pattern": "normal",
        "concern_level": "none",
        "inference_safe": True,
    }


# ============================================
# AI Input Sanitization
# ============================================

def sanitize_for_ai_input(
    mastery_score: Optional[float],
    participation_status: ParticipationStatus,
    excused_absence_count: int,
) -> dict:
    """
    Sanitize student data before sending to AI for insights.
    
    Prevents AI from making unfair inferences about students with valid absences.
    """
    if participation_status == ParticipationStatus.EXCUSED_ABSENT:
        return {
            "include_in_analysis": False,
            "reason": "excused_absence",
            "mastery_score": None,
            "note": "Exclude from analysis - valid absence",
        }
    
    if excused_absence_count > 5:
        return {
            "include_in_analysis": True,
            "mastery_score": mastery_score,
            "adjustment": "high_absence_context",
            "note": "Student has significant excused absences. Performance data may be limited.",
        }
    
    return {
        "include_in_analysis": True,
        "mastery_score": mastery_score,
        "adjustment": None,
    }


# ============================================
# Parent Portal Display
# ============================================

def format_attendance_for_parent(
    present_count: int,
    excused_count: int,
    unexcused_count: int,
) -> dict:
    """
    Format attendance data for parent portal.
    
    Clear distinction between absence types with explanatory note.
    """
    total = present_count + excused_count + unexcused_count
    attendance_rate = (present_count / total * 100) if total > 0 else 0
    
    return {
        "attendance": {
            "present": present_count,
            "excused_absent": excused_count,
            "unexcused_absent": unexcused_count,
            "total_days": total,
            "attendance_rate": round(attendance_rate, 1),
        },
        "note": "Excused absences do not affect academic performance calculations.",
        "explanation": {
            "excused_absent": "Approved absences (medical, family emergency, etc.) - not counted against academics",
            "unexcused_absent": "Unauthorized absences - may affect academic standing",
        },
    }
