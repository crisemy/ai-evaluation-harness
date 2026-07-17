from __future__ import annotations

import os
from pathlib import Path

from harness.providers.chat_completions import ChatCompletionsProvider
from harness.providers.ollama import OllamaProvider


def _load_dotenv(path: str = ".env") -> None:
    try:
        dotenv_path = Path(path)
        if not dotenv_path.exists():
            return
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


_load_dotenv()

PROVIDER_CONFIGS: dict[str, dict] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "provider_name": "groq",
        "pricing": {"input_price_per_1m": 0.59, "output_price_per_1m": 0.79},
        "max_retries": 3,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "provider_name": "openrouter",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/anomalyco/ai-evaluation-harness",
            "X-Title": "AI Evaluation Harness",
        },
        "pricing": {"input_price_per_1m": 0.50, "output_price_per_1m": 1.50},
        "max_retries": 3,
    },
}


def create_provider(name: str = "ollama") -> OllamaProvider | ChatCompletionsProvider:
    if name == "ollama":
        return OllamaProvider()

    config = PROVIDER_CONFIGS.get(name)
    if config is None:
        supported = ", ".join(["ollama"] + list(PROVIDER_CONFIGS))
        raise ValueError(f"Unknown provider '{name}'. Supported: {supported}")

    api_key = os.environ.get(config["api_key_env"])
    if not api_key:
        raise ValueError(
            f"Provider '{name}' requires {config['api_key_env']} environment variable"
        )

    return ChatCompletionsProvider(
        base_url=config["base_url"],
        api_key=api_key,
        provider_name=config["provider_name"],
        extra_headers=config.get("extra_headers"),
        pricing=config.get("pricing"),
        max_retries=config.get("max_retries", 3),
    )


__all__ = ["ChatCompletionsProvider", "OllamaProvider", "create_provider", "PROVIDER_CONFIGS"]
