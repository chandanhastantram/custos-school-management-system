"""
CUSTOS OpenAI Provider

OpenAI API integration.
"""

import json
from typing import Optional, Any

import openai
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.ai.base import AIProvider, AIResponse


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Generate text completion."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            content = response.choices[0].message.content or ""
            usage = response.usage
            
            return AIResponse(
                content=content,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                model=response.model,
                raw_response=response,
            )
        
        except openai.APIError as e:
            raise AIServiceError(
                message=f"OpenAI API error: {str(e)}",
                provider="openai",
                details={"error": str(e)},
            )
        except Exception as e:
            raise AIServiceError(
                message=f"AI generation failed: {str(e)}",
                provider="openai",
            )
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[dict, int]:
        """Generate JSON response."""
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\nYou must respond with valid JSON only. No markdown, no explanation, just JSON."
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature or 0.3,  # Lower temp for structured output
            max_tokens=max_tokens,
        )
        
        try:
            # Try to parse JSON
            content = response.content.strip()
            
            # Handle markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            
            parsed = json.loads(content)
            return parsed, response.total_tokens
        
        except json.JSONDecodeError as e:
            raise AIServiceError(
                message=f"Failed to parse AI response as JSON: {str(e)}",
                provider="openai",
                details={"raw_content": response.content[:500]},
            )


def get_ai_provider() -> AIProvider:
    """Get configured AI provider."""
    if settings.ai_provider == "openai":
        return OpenAIProvider()
    else:
        raise AIServiceError(f"Unknown AI provider: {settings.ai_provider}")
