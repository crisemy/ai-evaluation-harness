# Architecture

The AI Evaluation Harness is organized around several logical layers.

## Dataset Layer

Stores evaluation datasets, golden answers, and benchmark data.

## Execution Layer

The Execution Layer is responsible for running evaluations against supported AI providers.

Supported providers may include local and remote execution environments.

Examples include:

- Ollama
- OpenAI
- Anthropic
- Gemini
- OpenRouter
- DeepSeek API

Provider implementations should be abstracted behind a common interface.

## Evaluation Layer

Applies evaluation metrics and scoring mechanisms.

## Reporting Layer

Generates evaluation reports and quality dashboards.

## Observability Layer

Collects execution traces, metrics, logs, and diagnostic information.

## Integration Layer

Provides integration with CI/CD platforms and external systems.
