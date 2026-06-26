import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from harness.contracts.evaluation import EvaluationResult, MetricResult
from harness.contracts.execution import ExecutionResponse, TokenUsage
from harness.contracts.report import (
    EnvironmentInfo,
    EvaluationConfig,
    EvaluationSummary,
    MetricSummary,
    SummaryStats,
)
from harness.observability import (
    AlertEngine,
    AlertRule,
    DashboardGenerator,
    MetricSnapshot,
    TimeSeriesData,
    TimeSeriesStore,
)


@pytest.fixture
def eval_summary():
    now = datetime.now(timezone.utc)
    return EvaluationSummary(
        evaluation_name="test-eval",
        evaluation_id="eval-001",
        timestamp=now,
        duration_ms=1000,
        config=EvaluationConfig(
            dataset_path="test.json",
            dataset_format="json",
            provider="ollama",
            model="phi3",
            metrics=["exact_match"],
        ),
        environment=EnvironmentInfo(
            harness_version="0.1.0",
            python_version="3.12",
            platform="win32",
        ),
        summary=SummaryStats(
            total_entries=2,
            passed=1,
            failed=1,
            skipped=0,
            pass_rate=0.5,
            average_score=0.5,
            metrics={},
        ),
        results=[
            EvaluationResult(
                entry_id="e1",
                metrics=[
                    MetricResult(metric_name="exact_match", score=1.0, passed=True,
                                 explanation="match", threshold=0.5),
                ],
                overall_score=1.0,
                overall_passed=True,
                duration_ms=100,
                timestamp=now,
            ),
            EvaluationResult(
                entry_id="e2",
                metrics=[
                    MetricResult(metric_name="exact_match", score=0.0, passed=False,
                                 explanation="no match", threshold=0.5),
                ],
                overall_score=0.0,
                overall_passed=False,
                duration_ms=100,
                timestamp=now,
            ),
        ],
    )


class TestTimeSeriesStore:
    def test_record_and_read(self, eval_summary):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            path = f.name

        try:
            store = TimeSeriesStore(path)
            count = store.record(eval_summary)
            assert count == 2

            snapshots = store.read_all()
            assert len(snapshots) == 2
            assert all(s.metric_name == "exact_match" for s in snapshots)
            assert snapshots[0].score == 1.0
            assert snapshots[0].passed
            assert snapshots[1].score == 0.0
            assert not snapshots[1].passed
            assert snapshots[1].evaluation_id == "eval-001"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_record_multiple_times(self, eval_summary):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            path = f.name

        try:
            store = TimeSeriesStore(path)
            store.record(eval_summary)
            store.record(eval_summary)

            snapshots = store.read_all()
            assert len(snapshots) == 4
        finally:
            Path(path).unlink(missing_ok=True)

    def test_get_time_series(self, eval_summary):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            path = f.name

        try:
            store = TimeSeriesStore(path)
            store.record(eval_summary)

            series = store.get_time_series()
            assert len(series) == 1
            assert series[0].metric_name == "exact_match"
            assert len(series[0].snapshots) == 2
        finally:
            Path(path).unlink(missing_ok=True)

    def test_get_time_series_filtered(self, eval_summary):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            path = f.name

        try:
            store = TimeSeriesStore(path)
            store.record(eval_summary)

            series = store.get_time_series(metric_name="nonexistent")
            assert len(series) == 0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_read_empty_store(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            path = f.name

        try:
            store = TimeSeriesStore(path)
            assert store.read_all() == []
        finally:
            Path(path).unlink(missing_ok=True)

    def test_clear(self, eval_summary):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            path = f.name

        try:
            store = TimeSeriesStore(path)
            store.record(eval_summary)
            assert len(store.read_all()) == 2
            store.clear()
            assert store.read_all() == []
        finally:
            Path(path).unlink(missing_ok=True)

    def test_record_creates_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "subdir" / "metrics.ndjson"
            store = TimeSeriesStore(str(path))
            now = datetime.now(timezone.utc)
            summary = EvaluationSummary(
                evaluation_name="t", evaluation_id="e1", timestamp=now,
                duration_ms=0,
                config=EvaluationConfig("d", "json", "p", "m", ["x"]),
                environment=EnvironmentInfo("0.1", "3.12", "win32"),
                summary=SummaryStats(1, 1, 0, 0, 1.0, 1.0, {}),
                results=[
                    EvaluationResult("e1", [
                        MetricResult("x", 1.0, True, "", 0.5),
                    ], 1.0, True, 0, now),
                ],
            )
            count = store.record(summary)
            assert count == 1
            assert path.exists()


class TestAlertEngine:
    def test_add_and_remove_rule(self):
        engine = AlertEngine()
        assert engine.rules == []

        rule = AlertRule(name="test", metric_name="accuracy", operator="lt", threshold=0.5)
        engine.add_rule(rule)
        assert len(engine.rules) == 1

        assert engine.remove_rule("test")
        assert engine.rules == []

        assert not engine.remove_rule("nonexistent")

    def test_evaluate_triggers_alert(self):
        engine = AlertEngine()
        rule = AlertRule(name="low_score", metric_name="accuracy", operator="lt", threshold=0.5)
        engine.add_rule(rule)

        snapshots = [
            MetricSnapshot(
                metric_name="accuracy", score=0.3, passed=False, threshold=0.5,
                timestamp=datetime.now(timezone.utc), evaluation_id="e1",
            ),
        ]
        results = engine.evaluate(snapshots)
        assert len(results) == 1
        assert results[0].triggered
        assert results[0].rule_name == "low_score"

    def test_evaluate_does_not_trigger(self):
        engine = AlertEngine()
        rule = AlertRule(name="high_score", metric_name="accuracy", operator="lt", threshold=0.5)
        engine.add_rule(rule)

        snapshots = [
            MetricSnapshot(
                metric_name="accuracy", score=0.8, passed=True, threshold=0.5,
                timestamp=datetime.now(timezone.utc), evaluation_id="e1",
            ),
        ]
        results = engine.evaluate(snapshots)
        assert len(results) == 1
        assert not results[0].triggered

    def test_unknown_operator(self):
        engine = AlertEngine()
        rule = AlertRule(name="bad", metric_name="x", operator="unknown", threshold=0.5)
        engine.add_rule(rule)

        snapshots = [
            MetricSnapshot(metric_name="x", score=0.0, passed=False, threshold=0.5,
                           timestamp=datetime.now(timezone.utc), evaluation_id="e1"),
        ]
        results = engine.evaluate(snapshots)
        assert len(results) == 1
        assert not results[0].triggered

    def test_no_matching_snapshots(self):
        engine = AlertEngine()
        rule = AlertRule(name="no_match", metric_name="nonexistent", operator="lt", threshold=0.5)
        engine.add_rule(rule)

        snapshots = [
            MetricSnapshot(metric_name="other", score=0.0, passed=False, threshold=0.5,
                           timestamp=datetime.now(timezone.utc), evaluation_id="e1"),
        ]
        results = engine.evaluate(snapshots)
        assert results == []

    def test_evaluate_with_gt_operator(self):
        engine = AlertEngine()
        rule = AlertRule(name="too_high", metric_name="latency", operator="gt", threshold=1000)
        engine.add_rule(rule)

        snapshots = [
            MetricSnapshot(metric_name="latency", score=1500, passed=False, threshold=0,
                           timestamp=datetime.now(timezone.utc), evaluation_id="e1"),
        ]
        results = engine.evaluate(snapshots)
        assert len(results) == 1
        assert results[0].triggered

    def test_multiple_rules(self):
        engine = AlertEngine()
        engine.add_rule(AlertRule("r1", "m1", "lt", 0.5))
        engine.add_rule(AlertRule("r2", "m2", "gt", 100))

        snapshots = [
            MetricSnapshot("m1", 0.3, False, 0.5, datetime.now(timezone.utc), "e1"),
            MetricSnapshot("m2", 50, True, 0, datetime.now(timezone.utc), "e1"),
        ]
        results = engine.evaluate(snapshots)
        assert len(results) == 2
        assert results[0].triggered
        assert not results[1].triggered

    def test_default_rules(self):
        from harness.observability.alerts import DefaultAlertRules
        rules = DefaultAlertRules.get_defaults()
        assert len(rules) == 3
        assert all(isinstance(r, AlertRule) for r in rules)
        assert rules[0].name == "Low Pass Rate"

    def test_evaluate_uses_latest_snapshot(self):
        engine = AlertEngine()
        rule = AlertRule(name="trend", metric_name="m", operator="lt", threshold=0.5)
        engine.add_rule(rule)

        base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        snapshots = [
            MetricSnapshot("m", 0.8, True, 0.5, base, "e1"),
            MetricSnapshot("m", 0.2, False, 0.5, base.replace(second=1), "e2"),
            MetricSnapshot("m", 0.9, True, 0.5, base.replace(second=2), "e3"),
        ]
        result = engine.evaluate(snapshots, rules=[rule])
        assert len(result) == 1
        assert not result[0].triggered
        assert result[0].current_value == 0.9
        assert result[0].evaluation_id == "e3"


class TestDashboardGenerator:
    def test_generate_basic(self):
        gen = DashboardGenerator()
        html = gen.generate([], [])
        assert "<!DOCTYPE html>" in html
        assert "AI Evaluation Harness Dashboard" in html
        assert "</html>" in html

    def test_generate_with_time_series(self):
        gen = DashboardGenerator()
        now = datetime.now(timezone.utc)
        ts = TimeSeriesData(
            metric_name="exact_match",
            snapshots=[
                MetricSnapshot("exact_match", 0.8, True, 0.5, now, "e1"),
                MetricSnapshot("exact_match", 0.9, True, 0.5, now, "e2"),
            ],
        )
        html = gen.generate([ts], [])
        assert "exact_match" in html
        assert "0.80" in html or "0.8" in html

    def test_generate_with_alerts(self):
        gen = DashboardGenerator()
        from harness.observability import AlertResult
        now = datetime.now(timezone.utc)
        alerts = [
            AlertResult(rule_name="low_score", metric_name="accuracy", triggered=True,
                        current_value=0.3, threshold=0.5, operator="lt",
                        timestamp=now, message="TRIGGERED"),
        ]
        html = gen.generate([], alerts)
        assert "TRIGGERED" in html
        assert "low_score" in html

    def test_custom_title(self):
        from harness.observability import DashboardConfig
        cfg = DashboardConfig(title="Custom Dashboard")
        gen = DashboardGenerator(cfg)
        html = gen.generate([], [])
        assert "Custom Dashboard" in html

    def test_summary_cards_rendered(self):
        gen = DashboardGenerator()
        now = datetime.now(timezone.utc)
        ts = TimeSeriesData(
            metric_name="accuracy",
            snapshots=[MetricSnapshot("accuracy", 0.95, True, 0.5, now, "e1")],
        )
        html = gen.generate([ts], [])
        assert "summary-card" in html
        assert "0.95" in html
