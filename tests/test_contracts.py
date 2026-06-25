from datetime import datetime, timezone

from harness.contracts.dataset import Dataset, DatasetEntry, DatasetMetadata, Difficulty
from harness.contracts.evaluation import EvaluationResult, MetricResult
from harness.contracts.execution import (
    ExecutionRequest,
    ExecutionResponse,
    TokenUsage,
)
from harness.contracts.report import (
    EnvironmentInfo,
    EvaluationConfig,
    EvaluationSummary,
    MetricSummary,
    Report,
    ReportMetadata,
    SummaryStats,
)
from harness.contracts.trace import ObservableEvent, Trace


class TestDatasetContracts:
    def test_dataset_entry_required_fields(self):
        entry = DatasetEntry(id="test-1", input="Hello?", expected_output="Hi!")
        assert entry.id == "test-1"
        assert entry.input == "Hello?"
        assert entry.expected_output == "Hi!"
        assert entry.category is None
        assert entry.difficulty is None

    def test_dataset_entry_all_fields(self):
        entry = DatasetEntry(
            id="test-1",
            input="Hello?",
            expected_output="Hi!",
            category="greeting",
            difficulty=Difficulty.EASY,
            tags=["greeting", "test"],
            metadata={"source": "manual"},
        )
        assert entry.difficulty == Difficulty.EASY
        assert entry.tags == ["greeting", "test"]

    def test_dataset_construction(self):
        entries = [
            DatasetEntry(id="e1", input="Q1", expected_output="A1"),
            DatasetEntry(id="e2", input="Q2", expected_output="A2"),
        ]
        meta = DatasetMetadata(name="test-dataset")
        dataset = Dataset(metadata=meta, entries=entries)
        assert len(dataset.entries) == 2
        assert dataset.metadata.name == "test-dataset"

    def test_difficulty_enum_values(self):
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.MEDIUM.value == "medium"
        assert Difficulty.HARD.value == "hard"


class TestExecutionContracts:
    def test_execution_request_defaults(self):
        req = ExecutionRequest(
            entry_id="e1",
            prompt="Hello?",
            provider="ollama",
            model="llama3",
        )
        assert req.temperature == 0.7
        assert req.max_tokens == 1024
        assert req.top_p == 1.0
        assert req.stop_sequences == []

    def test_execution_response_construction(self):
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        now = datetime.now(timezone.utc)
        resp = ExecutionResponse(
            entry_id="e1",
            text="Hi!",
            provider="ollama",
            model="llama3",
            latency_ms=150,
            token_usage=usage,
            timestamp=now,
        )
        assert resp.text == "Hi!"
        assert resp.token_usage.total_tokens == 30
        assert resp.finish_reason == "stop"


class TestEvaluationContracts:
    def test_metric_result_passed(self):
        result = MetricResult(
            metric_name="exact_match",
            score=1.0,
            passed=True,
            explanation="Exact match",
            threshold=0.5,
        )
        assert result.passed is True
        assert result.score == 1.0

    def test_metric_result_failed(self):
        result = MetricResult(
            metric_name="exact_match",
            score=0.0,
            passed=False,
            explanation="No match",
            threshold=0.5,
        )
        assert result.passed is False

    def test_evaluation_result_aggregation(self):
        metrics = [
            MetricResult(
                metric_name="exact_match",
                score=1.0,
                passed=True,
                explanation="Match",
            ),
            MetricResult(
                metric_name="similarity",
                score=0.85,
                passed=True,
                explanation="Similar",
                threshold=0.7,
            ),
        ]
        now = datetime.now(timezone.utc)
        eval_result = EvaluationResult(
            entry_id="e1",
            metrics=metrics,
            overall_score=0.925,
            overall_passed=True,
            duration_ms=500,
            timestamp=now,
        )
        assert len(eval_result.metrics) == 2
        assert eval_result.overall_passed is True


class TestReportContracts:
    def test_evaluation_summary_construction(self):
        config = EvaluationConfig(
            dataset_path="./data.json",
            dataset_format="json",
            provider="ollama",
            model="llama3",
            metrics=["exact_match"],
        )
        env = EnvironmentInfo(
            harness_version="0.1.0",
            python_version="3.12",
            platform="win32",
        )
        metric_summary = MetricSummary(mean=0.8, min=0.0, max=1.0, pass_rate=0.75)
        stats = SummaryStats(
            total_entries=100,
            passed=75,
            failed=15,
            skipped=10,
            pass_rate=0.75,
            average_score=0.8,
            metrics={"exact_match": metric_summary},
        )
        now = datetime.now(timezone.utc)
        summary = EvaluationSummary(
            evaluation_name="test-run",
            evaluation_id="uuid-123",
            timestamp=now,
            duration_ms=5000,
            config=config,
            environment=env,
            summary=stats,
            results=[],
        )
        assert summary.summary.total_entries == 100
        assert summary.config.provider == "ollama"

    def test_report_construction(self):
        meta = ReportMetadata(format="json", generated_at=datetime.now(timezone.utc))
        report = Report(format="json", content='{"ok": true}', metadata=meta)
        assert report.format == "json"


class TestTraceContracts:
    def test_observable_event(self):
        now = datetime.now(timezone.utc)
        event = ObservableEvent(
            event_type="dataset_loaded",
            component="DatasetLoader",
            timestamp=now,
            data={"entry_count": 100},
            duration_ms=15,
        )
        assert event.event_type == "dataset_loaded"
        assert event.data["entry_count"] == 100

    def test_trace_construction(self):
        now = datetime.now(timezone.utc)
        events = [
            ObservableEvent(
                event_type="start",
                component="Orchestrator",
                timestamp=now,
                data={},
            )
        ]
        trace = Trace(trace_id="trace-1", evaluation_id="eval-1", events=events)
        assert len(trace.events) == 1
        assert trace.trace_id == "trace-1"
