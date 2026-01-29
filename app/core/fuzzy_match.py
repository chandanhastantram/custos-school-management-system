"""
CUSTOS Fuzzy Matching Utilities

Enhanced fuzzy matching for student identifiers from OCR results.
Handles common OCR errors, name variations, and roll number formats.
"""

import re
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

from thefuzz import fuzz, process


class StudentMatcher:
    """
    Fuzzy matcher for student identifiers.
    
    Handles:
    - Name variations (initials, nicknames)
    - OCR common errors (0/O, 1/l, etc.)
    - Roll number formats
    - Partial matches
    """
    
    # Common OCR character confusions
    OCR_CONFUSIONS = {
        '0': ['O', 'o', 'D', 'Q'],
        'O': ['0', 'o', 'D', 'Q'],
        '1': ['l', 'I', 'i', '|'],
        'l': ['1', 'I', 'i', '|'],
        'I': ['1', 'l', 'i', '|'],
        '5': ['S', 's'],
        'S': ['5', 's'],
        '8': ['B', 'b'],
        'B': ['8', 'b'],
        '6': ['G', 'b'],
        '2': ['Z', 'z'],
        'Z': ['2', 'z'],
    }
    
    def __init__(
        self,
        students: List[dict],
        name_field: str = "name",
        roll_field: str = "roll_number",
        id_field: str = "id",
        min_score: int = 70,
    ):
        """
        Initialize with student list.
        
        Args:
            students: List of student dicts with name/roll/id
            name_field: Key for student name
            roll_field: Key for roll number
            id_field: Key for unique ID
            min_score: Minimum fuzzy score (0-100) for match
        """
        self.students = students
        self.name_field = name_field
        self.roll_field = roll_field
        self.id_field = id_field
        self.min_score = min_score
        
        # Pre-normalize all student data
        self._normalized = self._prepare_student_data()
    
    def _prepare_student_data(self) -> dict:
        """Pre-process student data for matching."""
        normalized = {
            "by_roll": {},
            "by_name": {},
            "name_list": [],
            "roll_list": [],
        }
        
        for student in self.students:
            sid = student.get(self.id_field)
            name = student.get(self.name_field, "")
            roll = student.get(self.roll_field, "")
            
            # Normalize name
            norm_name = self._normalize_name(name)
            normalized["by_name"][norm_name] = student
            normalized["name_list"].append((norm_name, student))
            
            # Normalize roll number
            if roll:
                norm_roll = self._normalize_roll(str(roll))
                normalized["by_roll"][norm_roll] = student
                normalized["roll_list"].append((norm_roll, student))
                
                # Also store OCR variants
                for variant in self._generate_ocr_variants(norm_roll):
                    if variant not in normalized["by_roll"]:
                        normalized["by_roll"][variant] = student
        
        return normalized
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
        if not name:
            return ""
        
        # Lowercase and strip
        name = name.lower().strip()
        
        # Remove special characters except spaces
        name = re.sub(r'[^\w\s]', '', name)
        
        # Collapse multiple spaces
        name = re.sub(r'\s+', ' ', name)
        
        return name
    
    def _normalize_roll(self, roll: str) -> str:
        """Normalize a roll number for comparison."""
        if not roll:
            return ""
        
        # Uppercase and strip
        roll = roll.upper().strip()
        
        # Remove common separators
        roll = re.sub(r'[-_./\s]', '', roll)
        
        return roll
    
    def _generate_ocr_variants(self, text: str) -> List[str]:
        """Generate common OCR error variants of text."""
        variants = set()
        
        for i, char in enumerate(text):
            if char in self.OCR_CONFUSIONS:
                for replacement in self.OCR_CONFUSIONS[char]:
                    variant = text[:i] + replacement + text[i+1:]
                    variants.add(variant)
        
        return list(variants)
    
    def match(self, identifier: str) -> Optional[Tuple[dict, int, str]]:
        """
        Match an identifier to a student.
        
        Args:
            identifier: OCR'd student name or roll number
        
        Returns:
            Tuple of (student_dict, confidence_score, match_type) or None
        """
        if not identifier or not identifier.strip():
            return None
        
        identifier = identifier.strip()
        
        # Try exact roll number match first
        roll_match = self._match_roll_exact(identifier)
        if roll_match:
            return (roll_match, 100, "roll_exact")
        
        # Try fuzzy roll number match
        roll_match = self._match_roll_fuzzy(identifier)
        if roll_match:
            return roll_match
        
        # Try exact name match
        name_match = self._match_name_exact(identifier)
        if name_match:
            return (name_match, 100, "name_exact")
        
        # Try fuzzy name match
        name_match = self._match_name_fuzzy(identifier)
        if name_match:
            return name_match
        
        return None
    
    def _match_roll_exact(self, identifier: str) -> Optional[dict]:
        """Exact roll number match."""
        norm = self._normalize_roll(identifier)
        return self._normalized["by_roll"].get(norm)
    
    def _match_roll_fuzzy(self, identifier: str) -> Optional[Tuple[dict, int, str]]:
        """Fuzzy roll number match."""
        norm = self._normalize_roll(identifier)
        
        # Check if it looks like a roll number (has digits)
        if not any(c.isdigit() for c in norm):
            return None
        
        best_match = None
        best_score = 0
        
        for roll, student in self._normalized["roll_list"]:
            score = fuzz.ratio(norm, roll)
            if score > best_score and score >= self.min_score:
                best_score = score
                best_match = student
        
        if best_match:
            return (best_match, best_score, "roll_fuzzy")
        
        return None
    
    def _match_name_exact(self, identifier: str) -> Optional[dict]:
        """Exact name match."""
        norm = self._normalize_name(identifier)
        return self._normalized["by_name"].get(norm)
    
    def _match_name_fuzzy(self, identifier: str) -> Optional[Tuple[dict, int, str]]:
        """Fuzzy name match with multiple strategies."""
        norm = self._normalize_name(identifier)
        
        # Skip if too short
        if len(norm) < 3:
            return None
        
        best_match = None
        best_score = 0
        
        for stored_name, student in self._normalized["name_list"]:
            # Try different fuzzy algorithms
            scores = [
                fuzz.ratio(norm, stored_name),
                fuzz.partial_ratio(norm, stored_name),
                fuzz.token_sort_ratio(norm, stored_name),
                fuzz.token_set_ratio(norm, stored_name),
            ]
            
            # Use the best score from any algorithm
            max_score = max(scores)
            
            if max_score > best_score and max_score >= self.min_score:
                best_score = max_score
                best_match = student
        
        if best_match:
            return (best_match, best_score, "name_fuzzy")
        
        return None
    
    def match_bulk(
        self,
        identifiers: List[str],
    ) -> List[Tuple[str, Optional[dict], int, Optional[str]]]:
        """
        Match multiple identifiers.
        
        Returns:
            List of (original_identifier, student_or_none, score, match_type)
        """
        results = []
        
        for identifier in identifiers:
            match = self.match(identifier)
            if match:
                student, score, match_type = match
                results.append((identifier, student, score, match_type))
            else:
                results.append((identifier, None, 0, None))
        
        return results


def fuzzy_match_students(
    ocr_identifiers: List[str],
    students: List[dict],
    name_field: str = "name",
    roll_field: str = "roll_number",
    id_field: str = "id",
    min_score: int = 70,
) -> List[dict]:
    """
    Convenience function to match OCR identifiers to students.
    
    Args:
        ocr_identifiers: List of OCR'd identifiers
        students: List of student dicts
        name_field: Key for student name
        roll_field: Key for roll number
        id_field: Key for unique ID
        min_score: Minimum match score
    
    Returns:
        List of match result dicts with:
        - original: The original identifier
        - matched: True if matched
        - student_id: Matched student ID or None
        - student_name: Matched student name or None
        - confidence: Match confidence (0-100)
        - match_type: How matched (roll_exact, roll_fuzzy, name_exact, name_fuzzy)
    """
    matcher = StudentMatcher(
        students=students,
        name_field=name_field,
        roll_field=roll_field,
        id_field=id_field,
        min_score=min_score,
    )
    
    results = []
    for identifier in ocr_identifiers:
        match = matcher.match(identifier)
        
        if match:
            student, score, match_type = match
            results.append({
                "original": identifier,
                "matched": True,
                "student_id": student.get(id_field),
                "student_name": student.get(name_field),
                "student_roll": student.get(roll_field),
                "confidence": score,
                "match_type": match_type,
            })
        else:
            results.append({
                "original": identifier,
                "matched": False,
                "student_id": None,
                "student_name": None,
                "student_roll": None,
                "confidence": 0,
                "match_type": None,
            })
    
    return results


def extract_numeric_roll(text: str) -> Optional[str]:
    """Extract numeric roll number from text."""
    # Find all numeric sequences
    numbers = re.findall(r'\d+', text)
    
    if not numbers:
        return None
    
    # Return the longest numeric sequence (most likely to be roll number)
    return max(numbers, key=len)
