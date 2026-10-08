"""
LLM service for handling interactions with language models.
Supports multiple providers (Groq, OpenRouter, etc.) through a flexible provider system.
"""
import asyncio
import os
import logging
import httpx
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    OPENROUTER = "openrouter"


class LLMService:
    """Service for interacting with language model APIs."""

    PROVIDER_CONFIGS = {
        LLMProvider.GROQ: {
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "env_var": "GROQ_API_KEY",
            "default_model": "llama-3.3-70b-versatile",
            "timeout": 120.0
        },
        LLMProvider.OPENROUTER: {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "env_var": "OPENROUTER_API_KEY",
            "default_model": "openai/gpt-4o-mini",
            "timeout": 60.0
        }
    }

    def __init__(self, api_key: str = None, default_model: str = None,
                 provider: str = None, timeout: int = None):
        self.provider = None
        if provider:
            self.provider = LLMProvider(provider.lower())
        else:
            for p in [LLMProvider.GROQ, LLMProvider.OPENROUTER]:
                if os.getenv(self.PROVIDER_CONFIGS[p]["env_var"]):
                    self.provider = p
                    break
            if not self.provider:
                self.provider = LLMProvider.GROQ

        provider_config = self.PROVIDER_CONFIGS[self.provider]
        self.api_key = api_key or os.getenv(provider_config["env_var"], "")
        self.default_model = default_model or provider_config["default_model"]
        self.timeout = timeout or provider_config["timeout"]
        self.api_url = provider_config["url"]
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            self.logger.warning("No API key provided for %s. LLM service will not work.", self.provider)

    async def generate(self, prompt: str, temperature: float = 0.7,
                       model: Optional[str] = None, max_tokens: int = 2500,
                       system: Optional[str] = None, json_mode: bool = False) -> str:
        """Generate text using the LLM API."""
        if not self.api_key:
            self.logger.error("Cannot generate: No API key provided")
            return "Error: API key not configured."

        model = model or self.default_model
        self.logger.info("Generating text with model: %s", model)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
        }
        if json_mode and "gpt-oss" not in model:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for attempt in range(3):
                    response = await client.post(
                        self.api_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                    )
                    if response.status_code == 429 and attempt < 2:
                        self.logger.warning("Rate limited, waiting before retry %s", attempt + 1)
                        await asyncio.sleep(12)
                        continue
                    response.raise_for_status()
                    result = response.json()
                    if "choices" in result and result["choices"]:
                        return result["choices"][0]["message"]["content"]
                    self.logger.warning("Unexpected API response format")
                    return "Error: Unexpected response from LLM API"
                return "Error: LLM API request failed with status 429"
        except httpx.TimeoutException:
            self.logger.error("Timeout when calling LLM API with model %s", model)
            return "Error: The request to the LLM service timed out."
        except httpx.HTTPStatusError as e:
            self.logger.error("HTTP error when calling LLM API: %s", e)
            detail = (e.response.text or "")[:300]
            return f"Error: LLM API request failed with status {e.response.status_code}: {detail}"
        except Exception as e:
            self.logger.exception("Exception when calling LLM API: %s", e)
            return "Error: An unexpected error occurred when communicating with the LLM service."
