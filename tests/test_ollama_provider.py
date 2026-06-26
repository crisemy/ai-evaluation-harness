from unittest.mock import MagicMock, patch

import httpx
import pytest

from harness.contracts.execution import ExecutionRequest
from harness.providers.ollama import OllamaProvider, OllamaProviderError


@pytest.fixture
def provider():
    return OllamaProvider(base_url="http://test:11434", timeout=5.0)


@pytest.fixture
def request_():
    return ExecutionRequest(
        entry_id="test-001",
        prompt="What is the capital of France?",
        provider="ollama",
        model="phi3",
    )


class TestOllamaProvider:
    def test_provider_name(self, provider):
        assert provider.provider_name == "ollama"

    @patch("httpx.Client.get")
    def test_available_models(self, mock_get, provider):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "llama3.2"}, {"name": "gemma4"}]},
        )
        models = provider.available_models
        assert models == ["llama3.2", "gemma4"]
        mock_get.assert_called_once_with("/api/tags")

    @patch("httpx.Client.post")
    def test_generate_basic(self, mock_post, provider, request_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "model": "phi3",
                "created_at": "2026-06-25T12:00:00Z",
                "response": "Paris is the capital of France.",
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 10,
                "eval_count": 8,
                "total_duration": 1234567890,
            },
        )

        response = provider.generate(request_)

        assert response.entry_id == "test-001"
        assert response.text == "Paris is the capital of France."
        assert response.provider == "ollama"
        assert response.model == "phi3"
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 8
        assert response.token_usage.total_tokens == 18
        assert response.finish_reason == "stop"
        assert response.latency_ms >= 0

    @patch("httpx.Client.post")
    def test_generate_http_error(self, mock_post, provider, request_):
        mock_post.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )
        with pytest.raises(OllamaProviderError):
            provider.generate(request_)

    @patch("httpx.Client.post")
    def test_generate_empty_response(self, mock_post, provider, request_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "model": "llama3.2",
                "created_at": "",
                "response": "",
                "done": True,
                "prompt_eval_count": 0,
                "eval_count": 0,
            },
        )
        response = provider.generate(request_)
        assert response.text == ""
        assert response.token_usage.total_tokens == 0

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.stream")
    async def test_stream(self, mock_stream, provider, request_):
        chunks = [
            b'{"model":"llama3.2","response":"Paris","done":false}\n',
            b'{"model":"llama3.2","response":" is","done":false}\n',
            b'{"model":"llama3.2","response":" great","done":false}\n',
            b'{"model":"llama3.2","response":"","done":true,"done_reason":"stop"}\n',
        ]

        async def mock_aiter_lines():
            for c in chunks:
                yield c.decode()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = MagicMock()

        class AsyncClientCM:
            async def __aenter__(self):
                return mock_response
            async def __aexit__(self, *args):
                pass

        mock_stream.return_value = AsyncClientCM()

        tokens = []
        async for chunk in provider.stream(request_):
            tokens.append(chunk)

        assert len(tokens) == 4
        assert tokens[0].token == "Paris"
        assert tokens[-1].finish_reason == "stop"
