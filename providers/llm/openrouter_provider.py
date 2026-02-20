"""
OpenRouter LLM Provider
────────────────────────
Calls any model available on OpenRouter (https://openrouter.ai).
Uses the OpenAI-compatible /chat/completions endpoint.

Default model: minimax/minimax-m2 (set in pipeline.json)

Other models you can use via OpenRouter:
  minimax/minimax-m2
  minimax/minimax-m2.5   (if/when available on OpenRouter)
  anthropic/claude-opus-4
  openai/gpt-4o
  google/gemini-pro-1.5
  meta-llama/llama-3.1-405b
  mistralai/mistral-large
  ... see https://openrouter.ai/models for full list

Just change llm.model.openrouter in pipeline.json — no code changes needed.
"""
from __future__ import annotations
import sys as _sys
import os as _os
# Add the project root (this file's parent or grandparent) to sys.path
_this_file = _os.path.abspath(__file__)
_project_root = _os.path.dirname(_os.path.dirname(_this_file))  # goes up to AGC_4/
if _project_root not in _sys.path:
    _sys.path.insert(0, _project_root)
# Also add project root itself (for files directly in AGC_4/)
_self_dir = _os.path.dirname(_this_file)
if _self_dir not in _sys.path:
    _sys.path.insert(0, _self_dir)

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))

import json
import logging
import os

import aiohttp

from providers.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter provider — drop-in for any model on OpenRouter.
    Set OPENROUTER_API_KEY in your .env file.
    Set llm.model.openrouter in pipeline.json to choose the model.
    """

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY is not set. "
                "Get your key at https://openrouter.ai/keys and add it to .env"
            )
        # Optional: identifies your app in OpenRouter dashboard
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "https://github.com/your-repo")
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "YouTube AI Pipeline")

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def complete(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # JSON mode — not all OpenRouter models support it, so we only add when requested
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }

        logger.debug(f"[OpenRouter] Calling {self.model} ({max_tokens} max tokens)")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"OpenRouter error {resp.status} for model '{self.model}':\n{body}"
                    )
                data = await resp.json()

        # Parse response
        try:
            text = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})
            return LLMResponse(
                text=text,
                provider="openrouter",
                model=self.model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            )
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Unexpected OpenRouter response structure: {json.dumps(data)[:500]}"
            ) from exc
