from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from harness.contracts.dataset import DatasetEntry
from harness.contracts.evaluation import MetricResult
from harness.contracts.execution import ExecutionResponse
from harness.errors import HarnessError
from harness.evaluator import EvalSample, EvaluationConfigInput, EvaluationEngine
from harness.executor import ExecutorConfig, PromptExecutor
from harness.interfaces.dataset_loader import DatasetLoader
from harness.interfaces.metric import Metric
from harness.interfaces.provider import LLMProvider
from harness.loaders import JSONDatasetLoader
from harness.metrics import Contains, ExactMatch
from harness.providers import create_provider
from harness.reporters import JSONReporter

logger = logging.getLogger(__name__)


@dataclass
class ModelSpec:
    provider: str = "ollama"
    model: str = "phi3"
    temperature: float = 0.1
    max_tokens: int = 256


@dataclass
class CompareConfig:
    dataset_path: str
    models: list[ModelSpec]
    metrics: list[str] = field(default_factory=lambda: ["exact_match", "contains"])
    limit: int = 0


@dataclass
class ModelRunResult:
    spec: ModelSpec
    responses: list[ExecutionResponse]
    eval_summary: Any
    total_tokens: int
    total_latency_ms: int
    avg_latency_ms: float
    error: str | None = None


@dataclass
class ComparisonReport:
    dataset_path: str
    timestamp: datetime
    duration_ms: int
    total_entries: int
    results: list[ModelRunResult]

    def to_dict(self) -> dict:
        return {
            "type": "comparison",
            "dataset_path": self.dataset_path,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "total_entries": self.total_entries,
            "models": [
                {
                    "provider": r.spec.provider,
                    "model": r.spec.model,
                    "error": r.error,
                    "total_tokens": r.total_tokens,
                    "total_latency_ms": r.total_latency_ms,
                    "avg_latency_ms": round(r.avg_latency_ms, 1),
                    "pass_rate": round(r.eval_summary.summary.pass_rate * 100, 1) if r.eval_summary else 0,
                    "average_score": round(r.eval_summary.summary.average_score, 3) if r.eval_summary else 0,
                    "passed": r.eval_summary.summary.passed if r.eval_summary else 0,
                    "failed": r.eval_summary.summary.failed if r.eval_summary else 0,
                    "per_entry": [
                        {
                            "entry_id": resp.entry_id,
                            "response": resp.text[:200],
                            "latency_ms": resp.latency_ms,
                            "tokens": resp.token_usage.total_tokens,
                            "prompt_tokens": resp.token_usage.prompt_tokens,
                            "completion_tokens": resp.token_usage.completion_tokens,
                        }
                        for resp in r.responses
                    ],
                }
                for r in self.results
            ],
        }


class ComparisonEngine:
    def __init__(
        self,
        config: CompareConfig,
        loader: DatasetLoader | None = None,
    ):
        self._config = config
        self._loader = loader or JSONDatasetLoader()

    def run(self) -> ComparisonReport:
        start = time.monotonic()

        dataset = self._loader.load(self._config.dataset_path)
        entries = dataset.entries
        if self._config.limit > 0:
            entries = entries[: self._config.limit]

        logger.info("Loaded %d entries for comparison across %d models", len(entries), len(self._config.models))

        results: list[ModelRunResult] = []
        with ThreadPoolExecutor(max_workers=len(self._config.models)) as executor:
            futures = {
                executor.submit(self._run_model, spec, entries): spec
                for spec in self._config.models
            }
            for future in as_completed(futures):
                spec = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = "✓" if result.error is None else f"✗ {result.error}"
                    logger.info("Model %s: %s", spec.model, status)
                except Exception as e:
                    results.append(ModelRunResult(
                        spec=spec,
                        responses=[],
                        eval_summary=None,
                        total_tokens=0,
                        total_latency_ms=0,
                        avg_latency_ms=0,
                        error=str(e),
                    ))
                    logger.error("Model %s failed: %s", spec.model, e)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return ComparisonReport(
            dataset_path=self._config.dataset_path,
            timestamp=datetime.now(timezone.utc),
            duration_ms=elapsed_ms,
            total_entries=len(entries),
            results=results,
        )

    def _run_model(self, spec: ModelSpec, entries: list[DatasetEntry]) -> ModelRunResult:
        provider: LLMProvider = create_provider(spec.provider)
        executor_cfg = ExecutorConfig(
            provider=spec.provider,
            model=spec.model,
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
        )
        executor = PromptExecutor(self._loader, provider, executor_cfg)

        responses: list[ExecutionResponse] = []
        for entry in entries:
            logger.debug("  [%s] executing %s...", spec.model, entry.id)
            resp = executor.execute_entry(entry)
            responses.append(resp)

        total_tokens = sum(r.token_usage.total_tokens for r in responses)
        total_latency = sum(r.latency_ms for r in responses)
        avg_latency = total_latency / len(responses) if responses else 0

        metrics: list[Metric] = []
        for name in self._config.metrics:
            if name == "exact_match":
                metrics.append(ExactMatch())
            elif name == "contains":
                metrics.append(Contains())

        eval_cfg = EvaluationConfigInput(
            dataset_path=self._config.dataset_path,
            provider=spec.provider,
            model=spec.model,
            metrics=self._config.metrics,
        )
        engine = EvaluationEngine(metrics, eval_cfg)
        samples = [EvalSample(response=r, expected_output=entries[i].expected_output) for i, r in enumerate(responses)]
        summary = engine.evaluate(samples)

        return ModelRunResult(
            spec=spec,
            responses=responses,
            eval_summary=summary,
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
            avg_latency_ms=avg_latency,
        )
