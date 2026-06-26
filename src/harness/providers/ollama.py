from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

import httpx

from harness.contracts.execution import ExecutionRequest, ExecutionResponse, StreamChunk, TokenUsage
from harness.errors import HarnessError
from harness.interfaces.provider import LLMProvider

OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"


def _parse_timestamp(raw: str) -> datetime:
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return datetime.now(timezone.utc)


class OllamaProviderError(HarnessError):
    pass


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = OLLAMA_DEFAULT_BASE_URL, timeout: float = 120.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout)

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def available_models(self) -> list[str]:
        resp = self._client.get("/api/tags")
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]

    def generate(self, request: ExecutionRequest) -> ExecutionResponse:
        payload = self._build_payload(request, stream=False)
        start = time.monotonic()

        try:
            resp = self._client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise OllamaProviderError(f"Ollama API error: {e}") from e

        elapsed_ms = int((time.monotonic() - start) * 1000)

        text = data.get("response", "")
        token_usage = TokenUsage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0)),
        )

        timestamp = _parse_timestamp(data.get("created_at", ""))
        finish_reason = data.get("done_reason", "stop") or "stop"

        return ExecutionResponse(
            entry_id=request.entry_id,
            text=text,
            provider=self.provider_name,
            model=request.model,
            latency_ms=elapsed_ms,
            token_usage=token_usage,
            timestamp=timestamp,
            finish_reason=finish_reason,
            raw_response=data,
        )

    async def stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        payload = self._build_payload(request, stream=True)

        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
                async with client.stream("POST", "/api/generate", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        chunk_data = json.loads(line)
                        finish = chunk_data.get("done", False)
                        yield StreamChunk(
                            token=chunk_data.get("response", ""),
                            finish_reason=chunk_data.get("done_reason") if finish else None,
                        )
                        if finish:
                            return
        except httpx.HTTPError as e:
            raise OllamaProviderError(f"Ollama streaming error: {e}") from e

    def _build_payload(self, request: ExecutionRequest, stream: bool) -> dict[str, Any]:
        return {
            "model": request.model,
            "prompt": request.prompt,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p,
                "stop": request.stop_sequences or None,
            },
        }

    def close(self) -> None:
        self._client.close()
