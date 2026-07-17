from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


class ComparisonReportLoader:
    def __init__(self, report_path: str | Path):
        self._path = Path(report_path)
        with open(self._path) as f:
            self._data: dict[str, Any] = json.load(f)

    @property
    def dataset_path(self) -> str:
        return self._data.get("dataset_path", "")

    @property
    def timestamp(self) -> str:
        return self._data.get("timestamp", "")

    @property
    def total_entries(self) -> int:
        return self._data.get("total_entries", 0)

    @property
    def duration_ms(self) -> int:
        return self._data.get("duration_ms", 0)

    def to_dataframe(self) -> pd.DataFrame:
        rows: list[dict] = []
        for m in self._data.get("models", []):
            provider = m.get("provider", "?")
            model = m.get("model", "?")
            label = f"{provider}/{model}"
            cost = m.get("cost")
            rows.append({
                "label": label,
                "provider": provider,
                "model": model,
                "pass_rate": m.get("pass_rate", 0),
                "average_score": m.get("average_score", 0),
                "avg_latency_ms": m.get("avg_latency_ms", 0),
                "total_tokens": m.get("total_tokens", 0),
                "total_latency_ms": m.get("total_latency_ms", 0),
                "passed": m.get("passed", 0),
                "failed": m.get("failed", 0),
                "cost": cost if cost is not None else 0,
                "has_cost": cost is not None,
                "error": m.get("error"),
            })
        return pd.DataFrame(rows)

    def per_entry_df(self) -> pd.DataFrame:
        rows: list[dict] = []
        for m in self._data.get("models", []):
            provider = m.get("provider", "?")
            model = m.get("model", "?")
            label = f"{provider}/{model}"
            for entry in m.get("per_entry", []):
                cost = entry.get("cost")
                rows.append({
                    "label": label,
                    "provider": provider,
                    "model": model,
                    "entry_id": entry.get("entry_id", ""),
                    "response": entry.get("response", ""),
                    "latency_ms": entry.get("latency_ms", 0),
                    "tokens": entry.get("tokens", 0),
                    "prompt_tokens": entry.get("prompt_tokens", 0),
                    "completion_tokens": entry.get("completion_tokens", 0),
                    "cost": cost if cost is not None else 0,
                    "cost_label": f"${cost:.6f}" if cost is not None else "N/A",
                })
        return pd.DataFrame(rows)

    @classmethod
    def from_compare_command(
        cls,
        dataset: str,
        models: list[str],
        limit: int = 0,
    ) -> ComparisonReportLoader:
        import tempfile
        tmp = Path(tempfile.mkstemp(suffix=".json")[1])
        cmd = [
            sys.executable, "-m", "harness", "compare",
            "-d", dataset,
            "--models", *models,
            "-o", str(tmp),
        ]
        if limit:
            cmd.extend(["--limit", str(limit)])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"harness compare failed: {result.stderr}")
        return cls(tmp)

    @classmethod
    def historical_reports(cls, glob_pattern: str = ".harness/reports/comparison_report_*.json") -> list[dict]:
        reports: list[dict] = []
        for fpath in sorted(Path(".").glob(glob_pattern)):
            with open(fpath) as f:
                data = json.load(f)
            ts = data.get("timestamp", "")
            row: dict[str, Any] = {"filename": fpath.name, "timestamp": ts}
            for m in data.get("models", []):
                label = f"{m.get('provider', '?')}/{m.get('model', '?')}"
                cost = m.get("cost")
                row[f"{label}_pass_rate"] = m.get("pass_rate", 0)
                row[f"{label}_avg_latency_ms"] = m.get("avg_latency_ms", 0)
                row[f"{label}_cost"] = cost if cost is not None else 0
            reports.append(row)
        return reports
