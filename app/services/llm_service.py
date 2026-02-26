"""Centralized LLM service — singleton Anthropic client with usage tracking."""

import asyncio
import logging
import os
import time
import threading

from anthropic import Anthropic, AsyncAnthropic

logger = logging.getLogger(__name__)

# Model constants - use specific versions for production consistency
# See: https://docs.anthropic.com/en/docs/about-claude/models
MODEL_CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"  # Most intelligent (default)
MODEL_CLAUDE_35_HAIKU = "claude-3-5-haiku-20241022"    # Fastest, lowest cost
MODEL_CLAUDE_35_SONNET_LATEST = "claude-3-5-sonnet-latest"  # Auto-updates (dev only)

DEFAULT_MODEL = MODEL_CLAUDE_35_SONNET


class LLMService:
    """Lazy-init singleton wrapper around the Anthropic client."""

    def __init__(self):
        self._client: Anthropic | None = None
        self._async_client: AsyncAnthropic | None = None
        self._lock = threading.Lock()
        self._async_lock: asyncio.Lock | None = None
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    async def _get_async_client(self) -> AsyncAnthropic:
        if self._async_client is not None:
            return self._async_client
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        async with self._async_lock:
            if self._async_client is None:
                self._async_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._async_client

    # ── Sync API (kept for non-async callers) ──

    def generate(
        self,
        prompt: str,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 2000,
        system: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Simple text generation — returns the first text block as a string."""
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        if temperature is not None:
            kwargs["temperature"] = temperature

        start = time.time()
        response = self.client.messages.create(**kwargs)
        duration = time.time() - start

        self._track(response, model, duration)
        return response.content[0].text

    def create(self, **kwargs):
        """Full messages.create() pass-through — returns the Message object."""
        kwargs.setdefault("model", DEFAULT_MODEL)

        start = time.time()
        response = self.client.messages.create(**kwargs)
        duration = time.time() - start

        self._track(response, kwargs["model"], duration)
        return response

    # ── Async API ──

    async def agenerate(
        self,
        prompt: str,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 2000,
        system: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Async text generation — returns the first text block as a string."""
        client = await self._get_async_client()
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        if temperature is not None:
            kwargs["temperature"] = temperature

        start = time.time()
        response = await client.messages.create(**kwargs)
        duration = time.time() - start

        self._track(response, model, duration)
        return response.content[0].text

    async def acreate(self, **kwargs):
        """Async full messages.create() pass-through — returns the Message object."""
        client = await self._get_async_client()
        kwargs.setdefault("model", DEFAULT_MODEL)

        start = time.time()
        response = await client.messages.create(**kwargs)
        duration = time.time() - start

        self._track(response, kwargs["model"], duration)
        return response

    def _track(self, response, model: str, duration: float):
        usage = getattr(response, "usage", None)
        tokens_in = getattr(usage, "input_tokens", 0) if usage else 0
        tokens_out = getattr(usage, "output_tokens", 0) if usage else 0

        self.total_calls += 1
        self.total_input_tokens += tokens_in
        self.total_output_tokens += tokens_out

        logger.info(
            "LLM call: model=%s tokens_in=%d tokens_out=%d duration=%.2fs",
            model, tokens_in, tokens_out, duration,
        )

    def stats(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }


llm_service = LLMService()
