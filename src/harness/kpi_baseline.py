from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from harness.observability.store import TimeSeriesStore

logger = logging.getLogger(__name__)


class KPIVerdict(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


KPI_THRESHOLDS: dict[str, tuple[float, float, bool]] = {
    "pass_rate": (0.85, 0.70, True),
    "average_score": (0.85, 0.70, True),
    "hallucination_rate": (0.10, 0.20, False),
    "latency_ms": (500, 1000, False),
    "attack_success_rate": (10.0, 20.0, False),
}


def evaluate_kpi(metric_name: str, current: float, baseline: float | None) -> KPIVerdict:
    thresholds = KPI_THRESHOLDS.get(metric_name)
    if thresholds is None:
        return KPIVerdict.GREEN

    green_threshold, yellow_threshold, higher_is_better = thresholds

    if baseline is not None:
        if higher_is_better:
            if current >= green_threshold:
                return KPIVerdict.GREEN
            elif current >= yellow_threshold:
                return KPIVerdict.YELLOW
            else:
                return KPIVerdict.RED
        else:
            if current <= green_threshold:
                return KPIVerdict.GREEN
            elif current <= yellow_threshold:
                return KPIVerdict.YELLOW
            else:
                return KPIVerdict.RED

    if higher_is_better:
        return KPIVerdict.GREEN if current >= green_threshold else KPIVerdict.YELLOW
    else:
        return KPIVerdict.GREEN if current <= green_threshold else KPIVerdict.YELLOW


@dataclass
class BaselineSnapshot:
    metric_name: str
    score: float
    timestamp: datetime
    evaluation_id: str


@dataclass
class KPIComparison:
    metric_name: str
    current: float
    baseline: float | None
    verdict: KPIVerdict
    delta: float | None


@dataclass
class BaselineReport:
    timestamp: datetime
    comparisons: list[KPIComparison]
    overall_verdict: KPIVerdict
    summary: dict[str, Any]


class BaselineComparator:
    def __init__(self, store_path: str = ".harness/timeseries.ndjson"):
        self._store = TimeSeriesStore(store_path)

    def compare(self, current_metrics: dict[str, float]) -> BaselineReport:
        time_series = self._store.get_time_series()
        baselines: dict[str, float] = {}
        for ts in time_series:
            if ts.snapshots:
                baselines[ts.metric_name] = ts.snapshots[-1].score

        comparisons: list[KPIComparison] = []
        verdicts: list[KPIVerdict] = []

        for name, current in current_metrics.items():
            baseline = baselines.get(name)
            delta = (current - baseline) if baseline is not None else None
            verdict = evaluate_kpi(name, current, baseline)
            comparisons.append(KPIComparison(
                metric_name=name,
                current=current,
                baseline=baseline,
                verdict=verdict,
                delta=delta,
            ))
            verdicts.append(verdict)

        overall = KPIVerdict.RED if KPIVerdict.RED in verdicts else (
            KPIVerdict.YELLOW if KPIVerdict.YELLOW in verdicts else KPIVerdict.GREEN
        )

        return BaselineReport(
            timestamp=datetime.now(timezone.utc),
            comparisons=comparisons,
            overall_verdict=overall,
            summary={
                "total_metrics": len(comparisons),
                "green": sum(1 for c in comparisons if c.verdict == KPIVerdict.GREEN),
                "yellow": sum(1 for c in comparisons if c.verdict == KPIVerdict.YELLOW),
                "red": sum(1 for c in comparisons if c.verdict == KPIVerdict.RED),
                "overall": overall.value,
            },
        )

    @staticmethod
    def generate_report(report: BaselineReport, output_path: str) -> Path:
        data = {
            "timestamp": report.timestamp.isoformat(),
            "overall_verdict": report.overall_verdict.value,
            "summary": report.summary,
            "comparisons": [
                {
                    "metric": c.metric_name,
                    "current": c.current,
                    "baseline": c.baseline,
                    "verdict": c.verdict.value,
                    "delta": c.delta,
                }
                for c in report.comparisons
            ],
        }
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Baseline report written to %s", target)
        return target
