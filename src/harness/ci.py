from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from harness.observability.store import TimeSeriesStore


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
