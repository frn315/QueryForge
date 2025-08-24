"""
OpenAI provider for chat completions.
"""

import httpx
from typing import List, Dict, Any
from .config import Config

class OpenAIProvider:
    """OpenAI chat completion provider."""

    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def chat_completion(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1
    ) -> str:
        """Call OpenAI chat completion API."""

        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                error_detail = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_detail = error_data["error"].get("message", error_detail)
                except:
                    pass
                raise Exception(f"OpenAI API error: {error_detail}")

            data = response.json()

            if "choices" not in data or not data["choices"]:
                raise Exception("No response choices returned from OpenAI")

            return data["choices"][0]["message"]["content"].strip()

    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return Config.OPENAI_MODELS.copy()

    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        return Config.is_api_key_configured()