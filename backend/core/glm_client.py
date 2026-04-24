"""
Z.AI GLM Client

Wrapper for Z.AI GLM-4 API calls.
Compatible with OpenAI SDK format (per competition docs).

Author: Chip/Azim
"""

import httpx
import json
import os
import logging
from typing import Dict, Any, Optional
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Flag set when GLM returns 401 — avoids repeated failed calls in the same run
_GLM_UNAVAILABLE = False


class GLMClient:
    """Client for Z.AI GLM API"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GLM_API_KEY
        self.api_url = self.settings.GLM_API_URL
        self.model = self.settings.GLM_MODEL
        # Read fallback flag from .env  (GLM_FALLBACK_MODE=true)
        self.fallback_mode = os.getenv("GLM_FALLBACK_MODE", "false").lower() == "true"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to GLM.
        Falls back gracefully if the API key is expired/invalid.
        """
        global _GLM_UNAVAILABLE

        # Skip the API call if we already know GLM is unavailable this run
        if _GLM_UNAVAILABLE or self.fallback_mode:
            logger.warning("[GLM] Fallback mode — skipping API call")
            return {"choices": [{"message": {"content": "{}"}}], "_fallback": True}

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
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            status_code = e.response.status_code

            if status_code == 401:
                _GLM_UNAVAILABLE = True  # Don't retry in this process run
                logger.error(
                    "[GLM] 401 Token expired/invalid. "
                    "Get a fresh key via the competition activation email. "
                    "Set GLM_FALLBACK_MODE=true in .env to run in rule-based mode."
                )
                # Return empty fallback instead of crashing the pipeline
                return {"choices": [{"message": {"content": "{}"}}], "_fallback": True}

            if status_code == 429:
                logger.warning("[GLM] Rate limit hit — returning empty fallback")
                return {"choices": [{"message": {"content": "{}"}}], "_fallback": True}

            if status_code == 400:
                raise ValueError(f"Z.AI API request failed (400): {error_detail}")

            raise ValueError(f"Z.AI API error ({status_code}): {error_detail}")

        except httpx.ConnectError as e:
            logger.error(f"[GLM] Connection failed: {e}")
            return {"choices": [{"message": {"content": "{}"}}], "_fallback": True}

    async def extract_json(self, prompt: str) -> Dict[str, Any]:
        """
        Extract structured JSON from text using GLM.
        Returns an empty dict (not an error) if GLM is unavailable.
        """
        response = await self.chat_completion(
            prompt=prompt,
            temperature=0.3,
            response_format="json_object"
        )

        # Fallback response — return empty dict, caller handles it
        if response.get("_fallback"):
            return {}

        # Extract content from response
        content = response["choices"][0]["message"]["content"]

        try:
            result = json.loads(content)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
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
