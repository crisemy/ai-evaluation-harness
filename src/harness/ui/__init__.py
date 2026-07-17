from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def streamlit_app(
    report_path: str | None = None,
    dataset: str | None = None,
    models: list[str] | None = None,
    limit: int = 0,
    port: int = 8501,
) -> int:
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(Path(__file__).parent / "app.py"),
        "--server.port", str(port),
        "--server.headless", "true",
        "--",
    ]
    if report_path:
        cmd.extend(["--report", report_path])
    if dataset:
        cmd.extend(["--dataset", dataset])
    if models:
        cmd.extend(["--models"] + models)
    if limit:
        cmd.extend(["--limit", str(limit)])

    logger.info("Launching Streamlit dashboard on port %d ...", port)
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode
