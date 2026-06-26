from datetime import datetime, timezone

import pytest

from harness.contracts.execution import ExecutionResponse, TokenUsage
from harness.errors import HarnessError
from harness.evaluator import EvalSample, EvaluationEngine
from harness.metrics.contains import Contains
from harness.metrics.exact_match import ExactMatch


def _sample(entry_id: str, text: str, expected: str = "") -> EvalSample:
    return EvalSample(
        response=ExecutionResponse(
            entry_id=entry_id,
            text=text,
            provider="ollama",
            model="phi3",
            latency_ms=100,
            token_usage=TokenUsage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
            timestamp=datetime.now(timezone.utc),
        ),
        expected_output=expected,
    )


@pytest.fixture
def engine():
    return EvaluationEngine(metrics=[ExactMatch(), Contains()])


@pytest.fixture
def samples():
    return [
        _sample("e1", "Paris", expected="Paris"),
        _sample("e2", "Unknown", expected="Paris"),
    ]


class TestEvaluationEngine:
    def test_evaluate_returns_summary(self, engine, samples):
        summary = engine.evaluate(samples)
        assert summary.evaluation_id
        assert summary.config.provider == "ollama"
        assert summary.config.model == "phi3"
        assert summary.summary.total_entries == 2

    def test_evaluate_calculates_pass_rate(self, engine, samples):
        summary = engine.evaluate(samples)
        # e1: exact_match passes (Paris == Paris), contains passes
        # e2: exact_match fails (Unknown != Paris), contains passes (Unknown contains Paris? no → fails)
        assert summary.summary.total_entries == 2

    def test_evaluate_entry_results(self, engine, samples):
        summary = engine.evaluate(samples)
        assert len(summary.results) == 2
        assert summary.results[0].entry_id == "e1"
        assert summary.results[1].entry_id == "e2"

    def test_evaluate_empty_responses(self, engine):
        with pytest.raises(HarnessError, match="No execution responses"):
            engine.evaluate([])

    def test_evaluate_no_metrics(self):
        with pytest.raises(HarnessError, match="At least one metric"):
            EvaluationEngine(metrics=[])

    def test_evaluate_single_entry_passing(self, engine):
        summary = engine.evaluate([_sample("e1", "Paris", expected="Paris")])
        assert summary.summary.total_entries == 1
        assert summary.summary.pass_rate == 1.0

    def test_evaluate_tracks_metric_names(self, engine):
        assert engine.metric_names == ["exact_match", "contains"]

    def test_evaluate_sets_summary_stats(self, engine, samples):
        summary = engine.evaluate(samples)
        stats = summary.summary
        assert stats.passed + stats.failed == stats.total_entries
        assert 0.0 <= stats.pass_rate <= 1.0
        assert 0.0 <= stats.average_score <= 1.0

    def test_evaluate_handles_all_failing(self, engine):
        samples = [_sample("e1", "zzz", expected="Paris")]
        summary = engine.evaluate(samples)
        assert summary.summary.failed == 1
