"""
Transport layer for LLM API calls.

Supports two backends:
- OpenRouter (main track): Anthropic models via OpenRouter's unified API
- Ollama Cloud (open track): Local / open models via Ollama Cloud

Every call is instrumented with the telemetry collector automatically.
"""

import os
import json
import time
from typing import Optional
from dataclasses import dataclass

import requests


@dataclass
class LLMResponse:
    """Standardized response from any LLM transport."""
    text: str
    tokens_prompt: int
    tokens_completion: int
    model: str
    latency_sec: float
    error: Optional[str] = None


class TransportError(Exception):
    """Raised when an LLM transport call fails."""
    pass


class OpenRouterTransport:
    """OpenRouter API transport for the main track."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise TransportError("OPENROUTER_API_KEY not set")

    def chat(self, messages: list[dict], model: str, temperature: float = 0.0,
             max_tokens: int = 1024) -> LLMResponse:
        """Send a chat completion request."""
        t0 = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            latency = time.perf_counter() - t0

            choice = data["choices"][0]
            text = choice["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                text=text,
                tokens_prompt=usage.get("prompt_tokens", 0),
                tokens_completion=usage.get("completion_tokens", 0),
                model=model,
                latency_sec=latency,
            )
        except requests.RequestException as e:
            latency = time.perf_counter() - t0
            return LLMResponse(
                text="",
                tokens_prompt=0,
                tokens_completion=0,
                model=model,
                latency_sec=latency,
                error=str(e),
            )


class OllamaCloudTransport:
    """Ollama Cloud / local Ollama transport for the open track."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_key = api_key or os.environ.get("OLLAMA_CLOUD_API_KEY")

    def chat(self, messages: list[dict], model: str, temperature: float = 0.0,
             max_tokens: int = 1024) -> LLMResponse:
        """Send a chat completion request via Ollama API."""
        t0 = time.perf_counter()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                headers=headers,
                json=payload,
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()
            latency = time.perf_counter() - t0

            text = data.get("message", {}).get("content", "")
            # Ollama doesn't always return token counts; estimate if missing
            prompt_tokens = data.get("prompt_eval_count", self._estimate_tokens(messages))
            completion_tokens = data.get("eval_count", self._estimate_tokens(text))

            return LLMResponse(
                text=text,
                tokens_prompt=prompt_tokens,
                tokens_completion=completion_tokens,
                model=model,
                latency_sec=latency,
            )
        except requests.RequestException as e:
            latency = time.perf_counter() - t0
            return LLMResponse(
                text="",
                tokens_prompt=0,
                tokens_completion=0,
                model=model,
                latency_sec=latency,
                error=str(e),
            )

    @staticmethod
    def _estimate_tokens(text_or_messages) -> int:
        """Rough token estimate: ~4 chars per token."""
        if isinstance(text_or_messages, str):
            return len(text_or_messages) // 4
        total = 0
        for msg in text_or_messages:
            total += len(msg.get("content", "")) // 4
        return total


class TransportFactory:
    """Create the right transport for a given track."""

    @staticmethod
    def for_track(track: str):
        if track == "main":
            return OpenRouterTransport()
        elif track == "open":
            return OllamaCloudTransport()
        else:
            raise ValueError(f"Unknown track: {track}")
