"""
CUSTOS Fuzzy Matching for Student Identifiers

Improved matching for OCR-extracted names and roll numbers.
"""

from typing import Optional, List, Tuple
from uuid import UUID
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FuzzyMatcher:
    """
    Fuzzy matching for student identification.
    
    Features:
    - Levenshtein distance for name matching
    - Roll number pattern matching
    - Multiple identifier support
    - Confidence scoring
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self._students_cache: Optional[List[dict]] = None
    
    async def _load_students(self) -> List[dict]:
        """Load all students for tenant."""
        if self._students_cache is not None:
            return self._students_cache
        
        from app.users.models import User, UserRole
        
        query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        self._students_cache = []
        for user in users:
            student_data = {
                "id": user.id,
                "full_name": user.full_name or "",
                "email": user.email or "",
                "roll_number": None,
                "admission_number": None,
            }
            
            # Extract roll number from profile if available
            if hasattr(user, 'student_profile') and user.student_profile:
                profile = user.student_profile
                if hasattr(profile, 'roll_number'):
                    student_data["roll_number"] = profile.roll_number
                if hasattr(profile, 'admission_number'):
                    student_data["admission_number"] = profile.admission_number
            
            self._students_cache.append(student_data)
        
        return self._students_cache
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein (edit) distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """
        Calculate similarity score between 0 and 1.
        1.0 = exact match, 0.0 = completely different
        """
        if not s1 or not s2:
            return 0.0
        
        s1_clean = self._normalize(s1)
        s2_clean = self._normalize(s2)
        
        if s1_clean == s2_clean:
            return 1.0
        
        distance = self._levenshtein_distance(s1_clean, s2_clean)
        max_len = max(len(s1_clean), len(s2_clean))
        
        if max_len == 0:
            return 0.0
        
        return 1.0 - (distance / max_len)
    
    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (keep alphanumeric and space)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        return text
    
    def _extract_roll_number(self, identifier: str) -> Optional[str]:
        """Extract roll number pattern from identifier."""
        if not identifier:
            return None
        
        # Common roll number patterns
        patterns = [
            r'\b(\d{1,4})\b',           # Plain numbers: 1, 23, 456
            r'\b([A-Z]?\d{2,6})\b',      # Alphanumeric: A123, 2024001
            r'\b(\d{4}[A-Z]{1,3}\d{2,4})\b',  # Complex: 2024CS001
        ]
        
        for pattern in patterns:
            match = re.search(pattern, identifier.upper())
            if match:
                return match.group(1)
        
        return None
    
    async def match_student(
        self,
        identifier: str,
        min_confidence: float = 0.6,
    ) -> Tuple[Optional[UUID], float]:
        """
        Match identifier to a student.
        
        Returns (student_id, confidence_score)
        """
        if not identifier:
            return None, 0.0
        
        students = await self._load_students()
        
        identifier_clean = self._normalize(identifier)
        identifier_roll = self._extract_roll_number(identifier)
        
        best_match: Optional[UUID] = None
        best_score: float = 0.0
        
        for student in students:
            scores = []
            
            # Match by roll number (highest priority)
            if identifier_roll and student["roll_number"]:
                roll_clean = self._normalize(student["roll_number"])
                if identifier_roll.lower() == roll_clean:
                    scores.append(1.0)  # Exact roll number match
                elif self._similarity_score(identifier_roll, roll_clean) > 0.8:
                    scores.append(0.9)  # Close roll number match
            
            # Match by admission number
            if student["admission_number"]:
                adm_clean = self._normalize(student["admission_number"])
                if identifier_clean == adm_clean:
                    scores.append(0.95)
            
            # Match by full name
            if student["full_name"]:
                name_score = self._similarity_score(identifier_clean, student["full_name"])
                if name_score > 0.5:
                    scores.append(name_score)
                
                # Also try matching individual name parts
                name_parts = student["full_name"].lower().split()
                id_parts = identifier_clean.split()
                
                # Check if identifier contains first/last name
                for part in id_parts:
                    if len(part) >= 3:
                        for name_part in name_parts:
                            if part in name_part or name_part in part:
                                scores.append(0.7)
                                break
            
            # Match by email prefix
            if student["email"]:
                email_prefix = student["email"].split("@")[0].lower()
                email_score = self._similarity_score(identifier_clean, email_prefix)
                if email_score > 0.6:
                    scores.append(email_score * 0.8)
            
            # Calculate best score for this student
            if scores:
                max_score = max(scores)
                if max_score > best_score:
                    best_score = max_score
                    best_match = student["id"]
        
        if best_score >= min_confidence:
            return best_match, best_score
        
        return None, best_score
    
    async def match_students_batch(
        self,
        identifiers: List[str],
        min_confidence: float = 0.6,
    ) -> List[Tuple[str, Optional[UUID], float]]:
        """
        Match multiple identifiers.
        
        Returns list of (identifier, student_id, confidence)
        """
        results = []
        
        for identifier in identifiers:
            student_id, confidence = await self.match_student(
                identifier, min_confidence
            )
            results.append((identifier, student_id, confidence))
        
        return results
    
    async def suggest_matches(
        self,
        identifier: str,
        top_n: int = 5,
    ) -> List[Tuple[UUID, str, float]]:
        """
        Get top N possible matches for an identifier.
        
        Returns list of (student_id, student_name, confidence)
        """
        students = await self._load_students()
        
        identifier_clean = self._normalize(identifier)
        
        matches = []
        for student in students:
            name_score = self._similarity_score(
                identifier_clean, student["full_name"]
            )
            matches.append((student["id"], student["full_name"], name_score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[2], reverse=True)
        
        return matches[:top_n]
