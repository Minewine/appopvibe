"""
LLM service for handling interactions with language models.
Supports multiple providers (Groq, OpenRouter, etc.) through a flexible provider system.
"""
import os
import logging
import httpx
import asyncio
from typing import Dict, Any, Optional, List, Literal
from functools import lru_cache
from enum import Enum

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    OPENROUTER = "openrouter"
    # Add more providers as needed

class LLMService:
    """Service for interacting with language model APIs."""
    
    # Provider-specific configurations
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
            "default_model": "openai/gpt-3.5-turbo",
            "timeout": 60.0
        }
    }
    
    def __init__(self, api_key: str = None, default_model: str = None, 
                 provider: str = None, timeout: int = None):
        """Initialize the LLM service.
        
        Args:
            api_key: The API key for accessing the LLM provider (if None, will try to load from env)
            default_model: The default model to use (if None, will use provider default)
            provider: The LLM provider to use (groq, openrouter, etc.)
            timeout: Request timeout in seconds (if None, will use provider default)
        """
        # Determine provider (default to GROQ if available, then OPENROUTER)
        self.provider = None
        if provider:
            self.provider = LLMProvider(provider.lower())
        else:
            # Auto-detect based on available API keys
            for p in [LLMProvider.GROQ, LLMProvider.OPENROUTER]:
                if os.getenv(self.PROVIDER_CONFIGS[p]["env_var"]):
                    self.provider = p
                    break
            
            # Fall back to GROQ if no provider detected
            if not self.provider:
                self.provider = LLMProvider.GROQ
        
        # Get provider config
        provider_config = self.PROVIDER_CONFIGS[self.provider]
        
        # Set API key (explicit or from environment)
        self.api_key = api_key or os.getenv(provider_config["env_var"], "")
        
        # Set defaults from provider config if not specified
        self.default_model = default_model or provider_config["default_model"]
        self.timeout = timeout or provider_config["timeout"]
        self.api_url = provider_config["url"]
        
        self.logger = logging.getLogger(__name__)
        
        # Validate API key
        if not self.api_key:
            self.logger.warning(f"No API key provided for {self.provider}. LLM service will not work.")
    
    async def generate(self, prompt: str, temperature: float = 0.7, 
                      model: Optional[str] = None, max_tokens: int = 2048) -> str:
        """Generate text using the LLM API.
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Controls randomness (0-1)
            model: Model to use (defaults to self.default_model)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text string
        """
        if not self.api_key:
            self.logger.error("Cannot generate: No API key provided")
            return "Error: API key not configured."
            
        model = model or self.default_model
        self.logger.info(f"Generating text with model: {model}")
        
        try:
            # Use the configured provider's API endpoint
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,  # Use the provider-specific URL
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                else:
                    self.logger.warning("Unexpected API response format")
                    return "Error: Unexpected response from LLM API"
                
        except httpx.TimeoutException:
            self.logger.error(f"Timeout when calling LLM API with model {model}")
            return "Error: The request to the LLM service timed out."
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error when calling LLM API: {e}")
            return f"Error: LLM API request failed with status {e.response.status_code}"
        except Exception as e:
            self.logger.exception(f"Exception when calling LLM API: {e}")
            return "Error: An unexpected error occurred when communicating with the LLM service."
    
    @lru_cache(maxsize=32)
    async def cached_generate(self, prompt: str, temperature: float = 0.7,
                           model: Optional[str] = None) -> str:
        """Cached version of generate to avoid redundant API calls."""
        return await self.generate(prompt, temperature, model)
        
    async def generate_with_fallback(self, prompt: str, primary_model: str,
                                  backup_model: str, temperature: float = 0.7) -> str:
        """Try generating with primary model, fall back to backup if it fails."""
        try:
            return await self.generate(prompt, temperature, primary_model)
        except Exception as e:
            self.logger.warning(f"Primary model failed: {e}, trying backup model")
            return await self.generate(prompt, temperature, backup_model)
