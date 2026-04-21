"""
Z.AI GLM Client

Wrapper for Z.AI GLM-4-Flash API calls

Author: Chip/Azim
"""

import httpx
import json
from typing import Dict, Any, Optional
from backend.core.config import get_settings


class GLMClient:
    """Client for Z.AI GLM API"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GLM_API_KEY
        self.api_url = self.settings.GLM_API_URL
        self.model = self.settings.GLM_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to GLM

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., "json_object")

        Returns:
            API response dictionary
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format:
            payload["response_format"] = {"type": response_format}

        try:
            response = await self.client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "GLM API key is invalid or not set. "
                    "Please set GLM_API_KEY in .env file. "
                    "Current key: PLACEHOLDER_GLM_API_KEY_NOT_PROVIDED_YET"
                )
            raise

    async def extract_json(self, prompt: str) -> Dict[str, Any]:
        """
        Extract structured JSON from text using GLM

        Args:
            prompt: Prompt requesting JSON extraction

        Returns:
            Parsed JSON dictionary
        """
        response = await self.chat_completion(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for structured output
            response_format="json_object"
        )

        # Extract content from response
        content = response["choices"][0]["message"]["content"]

        # Parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw content
            return {"raw_content": content, "parse_error": True}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
_glm_client: Optional[GLMClient] = None


def get_glm_client() -> GLMClient:
    """Get or create GLM client instance"""
    global _glm_client
    if _glm_client is None:
        _glm_client = GLMClient()
    return _glm_client


async def close_glm_client():
    """Close the global GLM client"""
    global _glm_client
    if _glm_client is not None:
        await _glm_client.close()
        _glm_client = None
