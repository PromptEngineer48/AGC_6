"""Claude (Anthropic) LLM provider."""
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

import os
import anthropic
from providers.llm.base import BaseLLMProvider, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    def __init__(self, model: str):
        self.model = model
        self._client = anthropic.AsyncAnthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )

    @property
    def provider_name(self) -> str:
        return "claude"

    async def complete(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        kwargs: dict = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        # Claude doesn't have an explicit json_mode flag; we rely on prompt instructions
        response = await self._client.messages.create(**kwargs)
        usage = response.usage
        return LLMResponse(
            text=response.content[0].text,
            provider="claude",
            model=self.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )
