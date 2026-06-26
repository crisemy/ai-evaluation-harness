from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.contracts.report import Report, ReportMetadata
from harness.interfaces.reporter import Reporter


class _EnhancedEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


class JSONReporter(Reporter):
    def generate(
        self,
        summary,
        format: str = "json",
        options: dict[str, Any] | None = None,
    ) -> Report:
        opts = options or {}
        indent = opts.get("indent", 2)

        content = json.dumps(
            asdict(summary),
            cls=_EnhancedEncoder,
            indent=indent,
            ensure_ascii=False,
        )

        return Report(
            format="json",
            content=content,
            metadata=ReportMetadata(
                format="json",
                generated_at=datetime.now(timezone.utc),
            ),
        )

    def write(self, report: Report, path: str) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report.content, encoding="utf-8")
        return target
