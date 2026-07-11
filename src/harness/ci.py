from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from harness.kpi_baseline import KPIVerdict, BaselineComparator, BaselineReport
from harness.observability.store import TimeSeriesStore


class ReleaseVerdict(str, Enum):
    GO = "go"
    CONDITIONAL_GO = "conditional_go"
    NO_GO = "no_go"


@dataclass
class ReleaseReport:
    timestamp: datetime
    verdict: ReleaseVerdict
    kpi_report: BaselineReport | None = None
    risk_level: str = ""
    risk_score: float = 0.0
    asr: float | None = None
    coverage: float = 1.0
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "verdict": self.verdict.value,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "asr": self.asr,
            "coverage": self.coverage,
            "reasons": self.reasons,
            "kpi_verdict": self.kpi_report.overall_verdict.value if self.kpi_report else None,
            "kpi_summary": self.kpi_report.summary if self.kpi_report else None,
        }


class ReleaseReportGenerator:
    def __init__(self, store_path: str = ".harness/timeseries.ndjson"):
        self._store_path = store_path
        self._comparator = BaselineComparator(store_path)

    def generate(
        self,
        current_metrics: dict[str, float] | None = None,
        risk_level: str = "",
        risk_score: float = 0.0,
        asr: float | None = None,
        coverage: float = 1.0,
    ) -> ReleaseReport:
        kpi_report = self._comparator.compare(current_metrics or {}) if current_metrics else None

        reasons: list[str] = []
        verdict = ReleaseVerdict.GO

        if risk_level == "critical":
            verdict = ReleaseVerdict.NO_GO
            reasons.append(f"Risk level is CRITICAL (score={risk_score:.1f})")
        elif risk_level == "high":
            verdict = ReleaseVerdict.CONDITIONAL_GO
            reasons.append(f"Risk level is HIGH (score={risk_score:.1f}) — requires human override")
        elif risk_level == "medium":
            if kpi_report and kpi_report.overall_verdict == KPIVerdict.RED:
                verdict = ReleaseVerdict.CONDITIONAL_GO
                reasons.append("Medium risk with RED KPI verdict — requires review")

        if asr is not None and asr > 10.0:
            if verdict == ReleaseVerdict.GO:
                verdict = ReleaseVerdict.CONDITIONAL_GO
            reasons.append(f"Red team ASR {asr:.1f}% exceeds 10% threshold")

        if coverage < 0.9:
            if verdict == ReleaseVerdict.GO:
                verdict = ReleaseVerdict.CONDITIONAL_GO
            reasons.append(f"Evaluation coverage {coverage:.0%} below 90% minimum")

        if kpi_report:
            if kpi_report.overall_verdict == KPIVerdict.RED:
                verdict = ReleaseVerdict.NO_GO
                reasons.append("KPI baseline comparison: RED — blocking release")
            elif kpi_report.overall_verdict == KPIVerdict.YELLOW:
                if verdict == ReleaseVerdict.GO:
                    verdict = ReleaseVerdict.CONDITIONAL_GO
                reasons.append("KPI baseline comparison: YELLOW — monitor closely")

        return ReleaseReport(
            timestamp=datetime.now(timezone.utc),
            verdict=verdict,
            kpi_report=kpi_report,
            risk_level=risk_level,
            risk_score=risk_score,
            asr=asr,
            coverage=coverage,
            reasons=reasons,
        )

    @staticmethod
    def write(report: ReleaseReport, path: str) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        import json
        target.write_text(
            json.dumps(report.to_dict(), indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        return target


class BadgeGenerator:
    def generate(self, store_path: str, label: str = "pass rate") -> str:
        store = TimeSeriesStore(store_path)
        time_series = store.get_time_series()

        if not time_series:
            return self._render(label, "no data", "#9e9e9e")

        latest = max(
            (s for ts in time_series for s in ts.snapshots),
            key=lambda s: s.timestamp,
        )

        score = latest.score
        passed = latest.passed

        if passed:
            color = "#2e7d32"
            status = f"{score:.0%}"
        else:
            color = "#c62828"
            status = f"{score:.0%}"

        return self._render(label, status, color)

    @staticmethod
    def _render(label: str, value: str, color: str) -> str:
        label_esc = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        value_esc = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        label_width = max(60, len(label_esc) * 7 + 10)
        value_width = max(40, len(value_esc) * 7 + 10)
        total_width = label_width + value_width
        label_end = label_width
        value_end = label_width + value_width

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label_esc}: {value_esc}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_end}" height="20" fill="#555"/>
    <rect x="{label_end}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_end // 2}" y="15" fill="#010101" fill-opacity=".3">{label_esc}</text>
    <text x="{label_end // 2}" y="14">{label_esc}</text>
    <text x="{label_end + value_width // 2}" y="15" fill="#010101" fill-opacity=".3">{value_esc}</text>
    <text x="{label_end + value_width // 2}" y="14">{value_esc}</text>
  </g>
</svg>"""

    @staticmethod
    def write(svg: str, path: str) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg, encoding="utf-8")
        return target
