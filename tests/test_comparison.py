from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.comparison import CompareConfig, ComparisonEngine, ComparisonReport, ModelSpec, ModelRunResult
from harness.contracts.dataset import Dataset, DatasetEntry, DatasetMetadata
from harness.contracts.execution import ExecutionResponse, TokenUsage
from harness.contracts.report import EnvironmentInfo, EvaluationConfig, EvaluationSummary, MetricSummary, SummaryStats

FIXTURES = Path(__file__).parent / "fixtures"


def _mock_summary(pass_rate: float = 1.0, avg_score: float = 1.0, total: int = 1):
    return EvaluationSummary(
        evaluation_name="test",
        evaluation_id="test",
        timestamp=datetime.now(timezone.utc),
        duration_ms=100,
        config=EvaluationConfig(dataset_path="", dataset_format="json", provider="ollama", model="phi3", metrics=[]),
        environment=EnvironmentInfo(harness_version="0.1", python_version="3.12", platform="win32"),
        summary=SummaryStats(
            total_entries=total, passed=int(total * pass_rate),
            failed=total - int(total * pass_rate), skipped=0,
            pass_rate=pass_rate, average_score=avg_score,
            metrics={},
        ),
        results=[],
    )


def _mock_response(entry_id: str, text: str = "answer", tokens: int = 10, latency: int = 100) -> ExecutionResponse:
    return ExecutionResponse(
        entry_id=entry_id, text=text, provider="ollama", model="phi3",
        latency_ms=latency,
        token_usage=TokenUsage(prompt_tokens=5, completion_tokens=5, total_tokens=tokens),
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_config():
    return CompareConfig(
        dataset_path=str(FIXTURES / "sample_dataset.json"),
        models=[
            ModelSpec(model="phi3"),
            ModelSpec(model="llama3.2"),
        ],
    )


class TestComparisonEngine:
    @patch("harness.comparison.OllamaProvider")
    def test_run_with_mocked_provider(self, mock_provider_cls, sample_config):
        mock_provider = MagicMock()
        mock_provider.provider_name = "ollama"
        mock_provider_cls.return_value = mock_provider

        def mock_generate(req):
            return _mock_response(req.entry_id, text=f"response from {req.model}")

        mock_provider.generate.side_effect = mock_generate

        engine = ComparisonEngine(sample_config)
        report = engine.run()

        assert len(report.results) == 2
        assert any(r.spec.model == "phi3" for r in report.results)
        assert any(r.spec.model == "llama3.2" for r in report.results)

    @patch("harness.comparison.OllamaProvider")
    def test_report_contains_per_model_data(self, mock_provider_cls, sample_config):
        mock_provider = MagicMock()
        mock_provider.provider_name = "ollama"

        def mock_generate(req):
            return _mock_response(req.entry_id, text=f"resp from {req.model}", tokens=20, latency=50)

        mock_provider.generate.side_effect = mock_generate
        mock_provider_cls.return_value = mock_provider

        engine = ComparisonEngine(sample_config)
        report = engine.run()

        report_dict = report.to_dict()
        assert report_dict["total_entries"] == 3
        assert len(report_dict["models"]) == 2
        for model in report_dict["models"]:
            assert model["error"] is None
            assert model["total_tokens"] > 0

    def test_report_to_dict_structure(self):
        report = ComparisonReport(
            dataset_path="test.json",
            timestamp=datetime.now(timezone.utc),
            duration_ms=5000,
            total_entries=2,
            results=[
                ModelRunResult(
                    spec=ModelSpec(model="phi3"),
                    responses=[_mock_response("e1")],
                    eval_summary=_mock_summary(1.0, 1.0, 1),
                    total_tokens=10,
                    total_latency_ms=100,
                    avg_latency_ms=100.0,
                ),
            ],
        )
        d = report.to_dict()
        assert d["type"] == "comparison"
        assert len(d["models"]) == 1
        assert d["models"][0]["model"] == "phi3"
        assert d["models"][0]["pass_rate"] == 100.0

    def test_compare_config_defaults(self):
        config = CompareConfig(dataset_path="test.json", models=[ModelSpec()])
        assert config.metrics == ["exact_match", "contains"]
        assert config.limit == 0

    @patch("harness.comparison.OllamaProvider")
    def test_run_with_limit(self, mock_provider_cls):
        mock_provider = MagicMock()
        mock_provider.provider_name = "ollama"
        mock_provider.generate.return_value = _mock_response("e1")
        mock_provider_cls.return_value = mock_provider

        config = CompareConfig(
            dataset_path=str(FIXTURES / "sample_dataset.json"),
            models=[ModelSpec(model="phi3")],
            limit=1,
        )
        engine = ComparisonEngine(config)
        report = engine.run()
        assert report.total_entries == 1
