# src/comtrade_ingest/io/loaders.py

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from comtrade_ingest.utils.logger import get_logger

logger = get_logger("COMTRADE.IO")


def load_yaml(path: Path) -> dict[str, Any]:
    logger.debug("Loading YAML config from %s", path)

    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of YAML: {path}")

    return data