from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from harness.observability.models import AlertResult, DashboardConfig, MetricSnapshot, TimeSeriesData


class DashboardGenerator:
    def __init__(self, config: DashboardConfig | None = None):
        self._config = config or DashboardConfig()

    def generate(
        self,
        time_series: list[TimeSeriesData],
        alert_results: list[AlertResult] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        title = escape(self._config.title)

        sections: list[str] = [
            "<!DOCTYPE html>",
            f"<html lang='en'><head><meta charset='UTF-8'><title>{title}</title>",
            "<style>",
            "body{font-family:system-ui,sans-serif;max-width:1200px;margin:0 auto;padding:2rem;background:#f8f9fa;color:#333}",
            "h1{color:#1a1a2e;border-bottom:2px solid #e0e0e0;padding-bottom:0.5rem}",
            "h2{color:#16213e;margin-top:2rem}",
            "table{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.1);border-radius:8px;overflow:hidden}",
            "th,td{padding:0.75rem 1rem;text-align:left;border-bottom:1px solid #eee}",
            "th{background:#1a1a2e;color:#fff;font-weight:600}",
            "tr:hover{background:#f1f3f5}",
            ".passed{color:#2e7d32;font-weight:600}",
            ".failed{color:#c62828;font-weight:600}",
            ".alert-ok{color:#2e7d32}.alert-triggered{color:#c62828;font-weight:700}",
            ".summary-card{display:inline-block;background:#fff;border-radius:8px;padding:1.5rem;margin:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,.1);min-width:180px}",
            ".summary-card .value{font-size:2rem;font-weight:700;display:block}",
            ".summary-card .label{font-size:0.85rem;color:#666;margin-top:0.25rem}",
            ".badge{display:inline-block;padding:0.2rem 0.6rem;border-radius:4px;font-size:0.8rem;font-weight:600}",
            ".badge-ok{background:#e8f5e9;color:#2e7d32}",
            ".badge-triggered{background:#ffebee;color:#c62828}",
            "footer{margin-top:3rem;font-size:0.85rem;color:#999;text-align:center}",
            "</style></head><body>",
            f"<h1>{title}</h1>",
            f"<p>Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>",
        ]

        if time_series:
            sections.append(self._render_summary_cards(time_series))

        if alert_results:
            sections.append(self._render_alerts(alert_results))

        if time_series:
            sections.append(self._render_metrics_table(time_series))

        sections.append(
            "<footer>AI Evaluation Harness — Observability Dashboard</footer>"
        )
        sections.append("</body></html>")
        return "\n".join(sections)

    def _render_summary_cards(self, time_series: list[TimeSeriesData]) -> str:
        cards: list[str] = ['<h2>Summary</h2><div style="display:flex;flex-wrap:wrap">']
        for ts in time_series:
            if not ts.snapshots:
                continue
            latest = ts.snapshots[-1]
            trend = self._calculate_trend(ts.snapshots)
            cards.append(
                f"<div class='summary-card'>"
                f"<span class='value'>{latest.score:.2f}</span>"
                f"<span class='label'>{ts.metric_name}</span>"
                f"<span class='label' style='font-size:0.75rem'>{'↑' if trend > 0 else '↓' if trend < 0 else '→'} {abs(trend):.2f} last 10</span>"
                f"</div>"
            )
        cards.append("</div>")
        return "\n".join(cards)

    def _render_alerts(self, alert_results: list[AlertResult]) -> str:
        parts: list[str] = ['<h2>Alerts</h2><table><tr><th>Rule</th><th>Metric</th><th>Status</th><th>Value</th><th>Threshold</th><th>Message</th></tr>']
        for ar in alert_results:
            cls = "alert-triggered" if ar.triggered else "alert-ok"
            badge = "badge-triggered" if ar.triggered else "badge-ok"
            status_label = "TRIGGERED" if ar.triggered else "OK"
            parts.append(
                f"<tr class='{cls}'>"
                f"<td>{escape(ar.rule_name)}</td>"
                f"<td>{escape(ar.metric_name)}</td>"
                f"<td><span class='badge {badge}'>{status_label}</span></td>"
                f"<td>{ar.current_value:.3f}</td>"
                f"<td>{ar.threshold}</td>"
                f"<td>{escape(ar.message)}</td>"
                f"</tr>"
            )
        parts.append("</table>")
        return "\n".join(parts)

    def _render_metrics_table(self, time_series: list[TimeSeriesData]) -> str:
        parts: list[str] = ['<h2>Metric History</h2><table><tr><th>Metric</th><th>Latest</th><th>Avg (all)</th><th>Min</th><th>Max</th><th>Count</th><th>Trend</th></tr>']
        for ts in sorted(time_series, key=lambda t: t.metric_name):
            if not ts.snapshots:
                continue
            scores = [s.score for s in ts.snapshots]
            latest = scores[-1]
            avg_val = sum(scores) / len(scores)
            min_val = min(scores)
            max_val = max(scores)
            trend = self._calculate_trend(ts.snapshots)
            trend_str = f"{'↑' if trend > 0 else '↓' if trend < 0 else '→'} {abs(trend):.3f}"
            parts.append(
                f"<tr>"
                f"<td>{escape(ts.metric_name)}</td>"
                f"<td class='{'passed' if ts.snapshots[-1].passed else 'failed'}'>"
                f"{latest:.3f}</td>"
                f"<td>{avg_val:.3f}</td>"
                f"<td>{min_val:.3f}</td>"
                f"<td>{max_val:.3f}</td>"
                f"<td>{len(scores)}</td>"
                f"<td>{trend_str}</td>"
                f"</tr>"
            )
        parts.append("</table>")
        return "\n".join(parts)

    @staticmethod
    def _calculate_trend(snapshots: list[MetricSnapshot]) -> float:
        if len(snapshots) < 2:
            return 0.0
        recent = snapshots[-min(10, len(snapshots)):]
        if len(recent) < 2:
            return 0.0
        return recent[-1].score - recent[0].score
