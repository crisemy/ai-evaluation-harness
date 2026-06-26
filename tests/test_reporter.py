import json
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
from harness.reporters.json_reporter import JSONReporter


@pytest.fixture
def reporter():
    return JSONReporter()


@pytest.fixture
def sample_summary():
    return EvaluationSummary(
        evaluation_name="phi3-eval",
        evaluation_id="abc123",
        timestamp=datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc),
        duration_ms=5000,
        config=EvaluationConfig(
            dataset_path="datasets/test.json",
            dataset_format="json",
            provider="ollama",
            model="phi3",
            metrics=["exact_match"],
        ),
        environment=EnvironmentInfo(
            harness_version="0.1.0",
            python_version="3.12.7",
            platform="win32",
        ),
        summary=SummaryStats(
            total_entries=2,
            passed=1,
            failed=1,
            skipped=0,
            pass_rate=0.5,
            average_score=0.5,
            metrics={
                "exact_match": MetricSummary(mean=0.5, min=0.0, max=1.0, pass_rate=0.5),
            },
        ),
        results=[
            EvaluationResult(
                entry_id="e1",
                metrics=[
                    MetricResult(
                        metric_name="exact_match",
                        score=1.0,
                        passed=True,
                        explanation="Match",
                        threshold=0.5,
                    ),
                ],
                overall_score=1.0,
                overall_passed=True,
                duration_ms=100,
                timestamp=datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc),
            ),
            EvaluationResult(
                entry_id="e2",
                metrics=[
                    MetricResult(
                        metric_name="exact_match",
                        score=0.0,
                        passed=False,
                        explanation="No match",
                        threshold=0.5,
                    ),
                ],
                overall_score=0.0,
                overall_passed=False,
                duration_ms=100,
                timestamp=datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ],
    )


class TestJSONReporter:
    def test_generates_json_content(self, reporter, sample_summary):
        report = reporter.generate(sample_summary)
        assert report.format == "json"
        data = json.loads(report.content)
        assert data["evaluation_id"] == "abc123"
        assert data["summary"]["total_entries"] == 2
        assert data["summary"]["pass_rate"] == 0.5

    def test_writes_to_file(self, reporter, sample_summary, tmp_path):
        report = reporter.generate(sample_summary)
        output = tmp_path / "report.json"
        result_path = reporter.write(report, str(output))
        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "abc123" in content

    def test_custom_indent(self, reporter, sample_summary):
        report = reporter.generate(sample_summary, options={"indent": 4})
        lines = report.content.split("\n")
        # top-level key should be indented by 4 spaces
        assert any(line.startswith("    ") for line in lines)
