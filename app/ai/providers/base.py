"""
CUSTOS AI Base Provider
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
    ) -> dict:
        """Generate structured output."""
        pass
