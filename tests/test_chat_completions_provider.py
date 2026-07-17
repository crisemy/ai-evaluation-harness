from unittest.mock import MagicMock, patch

import httpx
import pytest

from harness.contracts.execution import ExecutionRequest
from harness.providers.chat_completions import ChatCompletionsProvider, ChatCompletionsProviderError


def _mock_chat_response(
    text: str = "Paris is the capital of France.",
    prompt_tokens: int = 14,
    completion_tokens: int = 8,
    total_tokens: int = 22,
    finish_reason: str = "stop",
) -> MagicMock:
    return MagicMock(
        status_code=200,
        json=lambda: {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "llama3-70b-8192",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        },
    )


@pytest.fixture
def provider():
    return ChatCompletionsProvider(
        base_url="https://api.test.com/v1",
        api_key="test-key",
        provider_name="groq",
        timeout=5.0,
    )


@pytest.fixture
def request_():
    return ExecutionRequest(
        entry_id="test-001",
        prompt="What is the capital of France?",
        provider="groq",
        model="llama3-70b-8192",
    )


class TestChatCompletionsProvider:
    def test_provider_name(self, provider):
        assert provider.provider_name == "groq"

    @patch("httpx.Client.get")
    def test_available_models(self, mock_get, provider):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "data": [
                    {"id": "llama3-70b-8192", "object": "model"},
                    {"id": "mixtral-8x7b-32768", "object": "model"},
                ]
            },
        )
        models = provider.available_models
        assert models == ["llama3-70b-8192", "mixtral-8x7b-32768"]
        mock_get.assert_called_once_with("/models")

    @patch("httpx.Client.post")
    def test_generate_basic(self, mock_post, provider, request_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "id": "chatcmpl-abc123",
                "object": "chat.completion",
                "created": 1700000000,
                "model": "llama3-70b-8192",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Paris is the capital of France.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 14,
                    "completion_tokens": 8,
                    "total_tokens": 22,
                },
            },
        )

        response = provider.generate(request_)

        assert response.entry_id == "test-001"
        assert response.text == "Paris is the capital of France."
        assert response.provider == "groq"
        assert response.model == "llama3-70b-8192"
        assert response.token_usage.prompt_tokens == 14
        assert response.token_usage.completion_tokens == 8
        assert response.token_usage.total_tokens == 22
        assert response.finish_reason == "stop"
        assert response.latency_ms >= 0

    @patch("httpx.Client.post")
    def test_generate_http_error(self, mock_post, provider, request_):
        mock_post.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
        )
        with pytest.raises(ChatCompletionsProviderError):
            provider.generate(request_)

    @patch("httpx.Client.post")
    def test_generate_empty_content(self, mock_post, provider, request_):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "id": "chatcmpl-xyz",
                "object": "chat.completion",
                "created": 1700000000,
                "model": "llama3-70b-8192",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": None},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 0, "total_tokens": 5},
            },
        )
        response = provider.generate(request_)
        assert response.text == ""
        assert response.token_usage.total_tokens == 5

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.stream")
    async def test_stream(self, mock_stream, provider, request_):
        chunks = [
            b"data: {\"choices\":[{\"delta\":{\"content\":\"Paris\"},\"index\":0}],\"usage\":null}\n",
            b"data: {\"choices\":[{\"delta\":{\"content\":\" is\"},\"index\":0}],\"usage\":null}\n",
            b"data: {\"choices\":[{\"delta\":{\"content\":\" great\"},\"index\":0}],\"usage\":null}\n",
            b"data: {\"choices\":[{\"delta\":{},\"index\":0,\"finish_reason\":\"stop\"}],\"usage\":null}\n",
            b"data: [DONE]\n",
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

    def test_build_payload(self, provider, request_):
        payload = provider._build_payload(request_, stream=False)
        assert payload["model"] == "llama3-70b-8192"
        assert payload["messages"] == [{"role": "user", "content": "What is the capital of France?"}]
        assert payload["stream"] is False
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 1024

    def test_extra_headers(self):
        prov = ChatCompletionsProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key="or-key",
            provider_name="openrouter",
            extra_headers={"HTTP-Referer": "https://example.com", "X-Title": "Test"},
        )
        assert prov._extra_headers["HTTP-Referer"] == "https://example.com"
        assert prov._extra_headers["X-Title"] == "Test"

    # --- Cost tracking tests (P3) ---

    @patch("httpx.Client.post")
    def test_generate_with_cost(self, mock_post, request_):
        prov = ChatCompletionsProvider(
            base_url="https://api.groq.com/openai/v1",
            api_key="gk-test",
            provider_name="groq",
            timeout=5.0,
            pricing={"input_price_per_1m": 0.59, "output_price_per_1m": 0.79},
        )
        mock_post.return_value = _mock_chat_response(
            text="Paris", prompt_tokens=100, completion_tokens=50, total_tokens=150
        )
        response = prov.generate(request_)
        expected_cost = (100 * 0.59 + 50 * 0.79) / 1_000_000
        assert response.token_usage.cost == pytest.approx(expected_cost, rel=1e-6)
        assert response.token_usage.prompt_tokens == 100
        assert response.token_usage.completion_tokens == 50

    @patch("httpx.Client.post")
    def test_generate_no_pricing(self, mock_post, provider, request_):
        mock_post.return_value = _mock_chat_response()
        response = provider.generate(request_)
        assert response.token_usage.cost is None

    def test_calculate_cost_with_pricing(self):
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1",
            api_key="test",
            provider_name="test",
            pricing={"input_price_per_1m": 1.0, "output_price_per_1m": 2.0},
        )
        cost = prov._calculate_cost(1000, 500)
        assert cost == (1000 * 1.0 + 500 * 2.0) / 1_000_000

    def test_calculate_cost_no_pricing(self):
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1", api_key="test", provider_name="test"
        )
        assert prov._calculate_cost(100, 50) is None

    # --- Retry / rate-limit tests (P4) ---

    @patch("httpx.Client.post")
    @patch("time.sleep")
    def test_retry_on_429_then_success(self, mock_sleep, mock_post, request_):
        mock_post.side_effect = [
            httpx.HTTPStatusError("429", request=MagicMock(), response=MagicMock(status_code=429)),
            _mock_chat_response(text="Paris", prompt_tokens=5, completion_tokens=5, total_tokens=10),
        ]
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1", api_key="test", provider_name="test",
            max_retries=3,
        )
        response = prov.generate(request_)
        assert response.text == "Paris"
        assert mock_post.call_count == 2

    @patch("httpx.Client.post")
    @patch("time.sleep")
    def test_retry_on_500_then_success(self, mock_sleep, mock_post, request_):
        mock_post.side_effect = [
            httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock(status_code=500)),
            _mock_chat_response(text="Paris"),
        ]
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1", api_key="test", provider_name="test",
            max_retries=3,
        )
        response = prov.generate(request_)
        assert response.text == "Paris"
        assert mock_post.call_count == 2

    @patch("httpx.Client.post")
    @patch("time.sleep")
    def test_retry_on_timeout_then_success(self, mock_sleep, mock_post, request_):
        mock_post.side_effect = [
            httpx.TimeoutException("timeout", request=MagicMock()),
            _mock_chat_response(text="Paris"),
        ]
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1", api_key="test", provider_name="test",
            max_retries=3,
        )
        response = prov.generate(request_)
        assert response.text == "Paris"
        assert mock_post.call_count == 2

    @patch("httpx.Client.post")
    @patch("time.sleep")
    def test_retry_exhaustion_429(self, mock_sleep, mock_post, request_):
        mock_post.side_effect = httpx.HTTPStatusError(
            "429", request=MagicMock(), response=MagicMock(status_code=429)
        )
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1", api_key="test", provider_name="test",
            max_retries=2,
        )
        with pytest.raises(ChatCompletionsProviderError, match="429"):
            prov.generate(request_)
        assert mock_post.call_count == 2

    @patch("httpx.Client.post")
    def test_no_retry_on_4xx_non_429(self, mock_post, request_):
        mock_post.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=MagicMock(status_code=400)
        )
        prov = ChatCompletionsProvider(
            base_url="https://api.test.com/v1", api_key="test", provider_name="test",
            max_retries=3,
        )
        with pytest.raises(ChatCompletionsProviderError, match="400"):
            prov.generate(request_)
        assert mock_post.call_count == 1
