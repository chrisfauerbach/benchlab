"""Async HTTP client for the Ollama API."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

from benchlab.config import OllamaConfig


@dataclass
class StreamChunk:
    """A parsed chunk from the Ollama streaming response."""

    content: str = ""
    thinking: str = ""
    done: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class OllamaResponse:
    """Aggregated response from a completed Ollama generation."""

    content: str = ""
    thinking: str = ""
    model: str = ""
    done: bool = True

    # Timing from Ollama response
    total_duration: int | None = None  # nanoseconds
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None

    # Client-side timing
    ttft_ms: float | None = None
    total_generation_ms: float | None = None


class OllamaClient:
    """Async client for interacting with the Ollama HTTP API."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout, connect=30.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        **options: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion, yielding chunks."""
        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if options:
            payload["options"] = options

        async with client.stream(
            "POST", "/api/chat", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                import json
                data = json.loads(line)
                msg = data.get("message", {})
                chunk = StreamChunk(
                    content=msg.get("content", ""),
                    thinking=msg.get("thinking", ""),
                    done=data.get("done", False),
                    raw=data,
                )
                yield chunk

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        **options: Any,
    ) -> OllamaResponse:
        """Run a chat completion with streaming, collecting the full response."""
        content_parts: list[str] = []
        thinking_parts: list[str] = []
        first_token_time: float | None = None
        start_time = time.perf_counter()
        final_raw: dict[str, Any] = {}

        async for chunk in self.chat_stream(model, messages, **options):
            if (chunk.content or chunk.thinking) and first_token_time is None:
                first_token_time = time.perf_counter()
            content_parts.append(chunk.content)
            thinking_parts.append(chunk.thinking)
            if chunk.done:
                final_raw = chunk.raw

        end_time = time.perf_counter()

        content = "".join(content_parts)
        thinking = "".join(thinking_parts)
        # For reasoning models that put everything in thinking, use that as content
        if not content.strip() and thinking.strip():
            content = thinking

        return OllamaResponse(
            content=content,
            thinking=thinking,
            model=final_raw.get("model", model),
            done=True,
            total_duration=final_raw.get("total_duration"),
            load_duration=final_raw.get("load_duration"),
            prompt_eval_count=final_raw.get("prompt_eval_count"),
            prompt_eval_duration=final_raw.get("prompt_eval_duration"),
            eval_count=final_raw.get("eval_count"),
            eval_duration=final_raw.get("eval_duration"),
            ttft_ms=(
                (first_token_time - start_time) * 1000
                if first_token_time
                else None
            ),
            total_generation_ms=(end_time - start_time) * 1000,
        )

    async def chat_no_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        **options: Any,
    ) -> OllamaResponse:
        """Run a chat completion without streaming."""
        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if options:
            payload["options"] = options

        start_time = time.perf_counter()
        resp = await client.post("/api/chat", json=payload)
        resp.raise_for_status()
        end_time = time.perf_counter()

        data = resp.json()
        msg = data.get("message", {})
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        if not content.strip() and thinking.strip():
            content = thinking
        return OllamaResponse(
            content=content,
            thinking=thinking,
            model=data.get("model", model),
            done=True,
            total_duration=data.get("total_duration"),
            load_duration=data.get("load_duration"),
            prompt_eval_count=data.get("prompt_eval_count"),
            prompt_eval_duration=data.get("prompt_eval_duration"),
            eval_count=data.get("eval_count"),
            eval_duration=data.get("eval_duration"),
            total_generation_ms=(end_time - start_time) * 1000,
        )

    async def pull_model(self, model: str) -> None:
        """Pull a model, waiting for completion."""
        client = await self._get_client()
        async with client.stream(
            "POST", "/api/pull", json={"name": model}
        ) as response:
            response.raise_for_status()
            async for _ in response.aiter_lines():
                pass

    async def list_models(self) -> list[dict[str, Any]]:
        """List locally available models."""
        client = await self._get_client()
        resp = await client.get("/api/tags")
        resp.raise_for_status()
        return resp.json().get("models", [])

    async def delete_model(self, model: str) -> None:
        """Delete a local model."""
        client = await self._get_client()
        resp = await client.request("DELETE", "/api/delete", json={"name": model})
        resp.raise_for_status()

    async def show_model(self, model: str) -> dict[str, Any]:
        """Get model details."""
        client = await self._get_client()
        resp = await client.post("/api/show", json={"name": model})
        resp.raise_for_status()
        return resp.json()
