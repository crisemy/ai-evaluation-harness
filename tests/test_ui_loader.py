from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.ui.loader import ComparisonReportLoader

FIXTURE = Path(__file__).parent / "fixtures" / "comparison_report.json"


@pytest.fixture
def loader() -> ComparisonReportLoader:
    return ComparisonReportLoader(FIXTURE)


class TestComparisonReportLoader:
    def test_loads_metadata(self, loader: ComparisonReportLoader):
        assert loader.dataset_path == "datasets/qa_kaggle.json"
        assert loader.total_entries == 5
        assert loader.duration_ms == 5000
        assert loader.timestamp == "2026-07-17T12:00:00"

    def test_to_dataframe_returns_all_models(self, loader: ComparisonReportLoader):
        df = loader.to_dataframe()
        assert list(df["label"]) == [
            "groq/llama-3.3-70b-versatile",
            "openrouter/openai/gpt-4o-mini",
            "ollama/phi3",
        ]

    def test_to_dataframe_columns(self, loader: ComparisonReportLoader):
        df = loader.to_dataframe()
        expected = {"label", "provider", "model", "pass_rate", "average_score",
                     "avg_latency_ms", "total_tokens", "passed", "failed", "cost", "has_cost"}
        assert expected.issubset(set(df.columns))

    def test_to_dataframe_cost_ollama_is_zero(self, loader: ComparisonReportLoader):
        df = loader.to_dataframe()
        ollama = df[df["provider"] == "ollama"].iloc[0]
        assert ollama["cost"] == 0
        assert ollama["has_cost"] == False

    def test_to_dataframe_cost_groq_is_positive(self, loader: ComparisonReportLoader):
        df = loader.to_dataframe()
        groq = df[df["provider"] == "groq"].iloc[0]
        assert groq["cost"] > 0
        assert groq["has_cost"] == True

    def test_per_entry_df_returns_all_entries(self, loader: ComparisonReportLoader):
        pdf = loader.per_entry_df()
        assert len(pdf) == 15  # 3 models × 5 entries
        assert list(pdf["entry_id"].unique()) == ["ci-001", "ci-002", "ci-003", "ci-004", "ci-005"]

    def test_per_entry_df_columns(self, loader: ComparisonReportLoader):
        pdf = loader.per_entry_df()
        expected = {"label", "entry_id", "response", "latency_ms", "tokens", "cost", "cost_label"}
        assert expected.issubset(set(pdf.columns))

    def test_per_entry_df_cost_label(self, loader: ComparisonReportLoader):
        pdf = loader.per_entry_df()
        ollama_rows = pdf[pdf["provider"] == "ollama"]
        assert all(c == "N/A" for c in ollama_rows["cost_label"])
        groq_rows = pdf[pdf["provider"] == "groq"]
        assert all(c.startswith("$") for c in groq_rows["cost_label"])

    def test_historical_reports_empty_when_no_files(self, loader: ComparisonReportLoader):
        reports = ComparisonReportLoader.historical_reports("nonexistent_*.json")
        assert reports == []

    def test_from_compare_command_raises_on_missing_dataset(self):
        with pytest.raises(RuntimeError, match="harness compare failed"):
            ComparisonReportLoader.from_compare_command(
                dataset="nonexistent.json",
                models=["ollama/phi3"],
            )
