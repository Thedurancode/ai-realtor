"""Centralized LLM service — singleton Anthropic client with usage tracking."""

import logging
import os
import time
import threading

from anthropic import Anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class LLMService:
    """Lazy-init singleton wrapper around the Anthropic client."""

    def __init__(self):
        self._client: Anthropic | None = None
        self._lock = threading.Lock()
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
