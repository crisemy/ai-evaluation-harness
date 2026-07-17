from __future__ import annotations

import json
import logging
import random
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

import httpx

from harness.contracts.execution import ExecutionRequest, ExecutionResponse, StreamChunk, TokenUsage
from harness.errors import HarnessError
from harness.interfaces.provider import LLMProvider

logger = logging.getLogger(__name__)


class ChatCompletionsProviderError(HarnessError):
    pass


class ChatCompletionsProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        provider_name: str = "openai-compatible",
        timeout: float = 120.0,
        extra_headers: dict[str, str] | None = None,
        pricing: dict[str, float] | None = None,
        max_retries: int = 3,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._provider_name = provider_name
        self._timeout = timeout
        self._extra_headers = extra_headers or {}
        self._pricing = pricing or {}
        self._max_retries = max_retries

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        headers.update(self._extra_headers)
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout, headers=headers)

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def available_models(self) -> list[str]:
        resp = self._client.get("/models")
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("data", [])]

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float | None:
        if not self._pricing:
            return None
        input_price = self._pricing.get("input_price_per_1m", 0)
        output_price = self._pricing.get("output_price_per_1m", 0)
        if input_price == 0 and output_price == 0:
            return None
        return (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000

    def generate(self, request: ExecutionRequest) -> ExecutionResponse:
        payload = self._build_payload(request, stream=False)
        start = time.monotonic()

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                last_error = None
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code
                if status == 429 and attempt < self._max_retries - 1:
                    delay = 1.0 * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        "Rate limited (429) on attempt %d/%d — retrying in %.1fs",
                        attempt + 1, self._max_retries, delay,
                    )
                    time.sleep(delay)
                    continue
                if status >= 500 and attempt < self._max_retries - 1:
                    delay = 1.0 * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        "Server error (%d) on attempt %d/%d — retrying in %.1fs",
                        status, attempt + 1, self._max_retries, delay,
                    )
                    time.sleep(delay)
                    continue
                raise ChatCompletionsProviderError(
                    f"ChatCompletions API error (HTTP {status}): {e}"
                ) from e
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = 1.0 * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        "Timeout on attempt %d/%d — retrying in %.1fs",
                        attempt + 1, self._max_retries, delay,
                    )
                    time.sleep(delay)
                    continue
            except httpx.HTTPError as e:
                raise ChatCompletionsProviderError(f"ChatCompletions API error: {e}") from e

        if last_error is not None:
            raise ChatCompletionsProviderError(
                f"ChatCompletions API error after {self._max_retries} retries: {last_error}"
            ) from last_error

        elapsed_ms = int((time.monotonic() - start) * 1000)

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "") or ""

        usage_raw = data.get("usage", {}) or {}
        prompt_tokens = usage_raw.get("prompt_tokens", 0)
        completion_tokens = usage_raw.get("completion_tokens", 0)
        total_tokens = usage_raw.get("total_tokens", 0)

        cost = self._calculate_cost(prompt_tokens, completion_tokens)

        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )

        finish_reason = choice.get("finish_reason", "stop") or "stop"

        return ExecutionResponse(
            entry_id=request.entry_id,
            text=text,
            provider=self._provider_name,
            model=request.model,
            latency_ms=elapsed_ms,
            token_usage=token_usage,
            timestamp=datetime.now(timezone.utc),
            finish_reason=finish_reason,
            raw_response=data,
        )

    async def stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        payload = self._build_payload(request, stream=True)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        headers.update(self._extra_headers)

        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout, headers=headers) as client:
                async with client.stream("POST", "/chat/completions", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        raw = line[6:]
                        if raw == "[DONE]":
                            return
                        chunk_data = json.loads(raw)
                        choice = chunk_data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        token = delta.get("content", "") or ""
                        finish = choice.get("finish_reason")
                        yield StreamChunk(token=token, finish_reason=finish)
                        if finish:
                            return
        except httpx.HTTPError as e:
            raise ChatCompletionsProviderError(f"ChatCompletions streaming error: {e}") from e

    def _build_payload(self, request: ExecutionRequest, stream: bool) -> dict[str, Any]:
        return {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stop": request.stop_sequences or None,
            "stream": stream,
        }

    def close(self) -> None:
        self._client.close()
