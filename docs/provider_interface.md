# Provider Interface Specification

This document defines the abstract contract that all LLM providers must implement. Following the CORE framework's data contract patterns (`ai-qa-core-framework/01_fundamentals/data_contracts.md`).

---

## 1. Core Interface

```python
class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Send a prompt to the provider and return the response."""
        pass

    @abstractmethod
    def stream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]:
        """Stream a response from the provider token by token."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'ollama', 'openai')."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """Return list of available model identifiers."""
        pass
```

---

## 2. Data Structures

### 2.1 GenerateRequest

```python
@dataclass
class GenerateRequest:
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    extra_params: dict = field(default_factory=dict)
```

### 2.2 GenerateResponse

```python
@dataclass
class GenerateResponse:
    text: str
    provider: str
    model: str
    latency_ms: int
    token_usage: TokenUsage
    finish_reason: str
    raw_response: dict  # provider-specific full response
```

### 2.3 TokenUsage

```python
@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float | None = None  # provider-dependent
```

### 2.4 StreamChunk

```python
@dataclass
class StreamChunk:
    token: str
    finish_reason: str | None = None
```

---

## 3. Provider Configuration

Providers are configured via a unified configuration schema:

```json
{
  "providers": {
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "default_model": "llama3",
      "timeout_seconds": 30,
      "max_retries": 3
    },
    "openai": {
      "enabled": false,
      "api_key": "${OPENAI_API_KEY}",
      "default_model": "gpt-4o",
      "organization": null,
      "timeout_seconds": 60,
      "max_retries": 3
    },
    "anthropic": {
      "enabled": false,
      "api_key": "${ANTHROPIC_API_KEY}",
      "default_model": "claude-3-opus",
      "timeout_seconds": 60,
      "max_retries": 2
    }
  }
}
```

All secrets must use environment variable references (`${VAR_NAME}`). No plain-text secrets in configuration files.

---

## 4. Provider Registry

The registry manages available provider instances:

```python
class ProviderRegistry:
    def register(self, name: str, provider: LLMProvider) -> None: ...
    def get(self, name: str) -> LLMProvider: ...
    def list_available(self) -> list[str]: ...
    def is_available(self, name: str) -> bool: ...
```

---

## 5. Error Handling

| Error | Trigger | Retry | Fallback |
|-------|---------|-------|----------|
| `TimeoutError` | Response exceeds timeout | Yes (configurable count) | Skip entry |
| `AuthError` | Invalid or missing credentials | No | Abort evaluation |
| `RateLimitError` | Provider rate limit hit | Yes (exponential backoff) | Skip entry |
| `ModelError` | Requested model unavailable | No | Skip entry |
| `ProviderError` | Provider returns error status | Yes | Skip entry |

Error taxonomy follows CORE data contract patterns for failure classification.

---

## 6. Provider Implementations

### 6.1 Ollama (Reference Implementation)

- Local-only, no authentication
- Default provider for development and testing
- Supports all OpenAI-compatible parameters

### 6.2 OpenAI

- API-key based authentication
- Supports chat completions and streaming
- Token usage tracking with cost estimation

### 6.3 Anthropic

- API-key based authentication
- Supports messages API with streaming
- Different parameter naming (max_tokens vs max_tokens_to_sample)

### 6.4 Future Providers

| Provider | Status | Notes |
|----------|--------|-------|
| Gemini | Planned | Google AI SDK |
| OpenRouter | Planned | Unified API for multiple models |
| DeepSeek | Planned | API or local via Ollama |
| vLLM | Future | High-throughput local serving |

---

## 7. Testing Guidelines

- Every provider must have a mock implementation for unit tests
- Contract tests must verify all error types for each provider
- Integration tests must run against at least one real provider (Ollama by default)
- Provider-specific parameter mapping must be tested with known input-output pairs
