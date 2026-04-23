from __future__ import annotations

import logging
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter


def configure_logging(log_level: str, logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(log_level.upper())

    console = logging.StreamHandler()
    console.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root_logger.addHandler(console)
