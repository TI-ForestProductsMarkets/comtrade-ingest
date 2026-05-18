"""
Shared utility functions for Comtrade download modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from comtrade_ingest.io.paths import resolve_path
from comtrade_ingest.utils.logger import get_logger

logger = get_logger("COMTRADE.UTILS")


def load_yaml(path: Path) -> dict[str, Any]:
    logger.debug("Loading YAML config from %s", path)

    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of YAML: {path}")

    return data


def get_output_dir(section_cfg: dict[str, Any], default: str) -> Path:
    output_cfg = section_cfg.get("output", {})
    if not isinstance(output_cfg, dict):
        output_cfg = {}

    directory = output_cfg.get("directory", default)
    return resolve_path(str(directory))


def get_manifest_name(section_cfg: dict[str, Any], default: str) -> str:
    output_cfg = section_cfg.get("output", {})
    if not isinstance(output_cfg, dict):
        output_cfg = {}

    return str(output_cfg.get("manifest_file", default))


def get_manifest_path(section_cfg: dict[str, Any], default_dir: str, default_name: str) -> Path:
    output_dir = get_output_dir(section_cfg, default_dir)
    manifest_name = get_manifest_name(section_cfg, default_name)
    return output_dir / manifest_name


def get_single_manifest_path(single_cfg: dict[str, Any]) -> Path:
    return get_manifest_path(
        section_cfg=single_cfg,
        default_dir="data/raw/api/single",
        default_name="download_manifest_single.json",
    )


def get_bulk_manifest_path(bulk_cfg: dict[str, Any]) -> Path:
    return get_manifest_path(
        section_cfg=bulk_cfg,
        default_dir="data/raw/api/bulk",
        default_name="download_manifest_bulk.json",
    )


def write_manifest(rows: list[dict[str, Any]], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    logger.info("Manifest written to: %s", manifest_path)


def load_api_files_from_manifest(manifest_path: Path) -> list[Path]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file does not exist: {manifest_path}")

    rows = json.loads(manifest_path.read_text(encoding="utf-8"))

    if not isinstance(rows, list):
        raise ValueError(f"Expected manifest to contain a list: {manifest_path}")

    files: list[Path] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        if row.get("status") not in {"downloaded", "skipped"}:
            continue

        output_paths = row.get("output_paths")
        if isinstance(output_paths, list):
            files.extend(Path(path) for path in output_paths)
            continue

        output_path = row.get("output_path")
        if output_path:
            files.append(Path(output_path))

    return files

## Usage: output_file = format_output_file(job.output_file, job.params)
def format_output_file(template: str, params: dict[str, Any]) -> str:
    try:
        return template.format(**params)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(
            f"output_file template references missing parameter: {missing}"
        ) from exc


def log_config_warnings(cfg: ComtradeConfig) -> None:

    if cfg.single.enabled and cfg.bulk.enabled:
        logger.warning(
            "Both single.enabled and bulk.enabled are true; both types of jobs will run."
        )

    if not cfg.single.enabled and cfg.single.jobs:
        logger.warning(
            "single.enabled=false; configured single jobs will be ignored."
        )

    if not cfg.bulk.enabled and cfg.bulk.jobs:
        logger.warning(
            "bulk.enabled=false; configured bulk jobs will be ignored."
        )

    if cfg.runtime.max_workers > 12:
        logger.warning(
            "max_workers=%d is relatively high. If you see HTTP 429 rate limits, reduce it.",
            cfg.runtime.max_workers,
        )

    if cfg.retry.rate_limit_max_attempts <= 0:
        logger.warning(
            "rate_limit.max_attempts=%d; HTTP 429 retries are disabled.",
            cfg.retry.rate_limit_max_attempts,
        )

    if str(cfg.log_level).upper() == "DEBUG":
        logger.warning(
            "log_level=DEBUG can create large log files for bigger runs."
        )

    if not cfg.runtime.overwrite_existing:
        logger.info(
            "overwrite_existing=false; valid existing output files will be skipped."
        )

    if cfg.auth.enabled and cfg.auth.env_file:
        logger.info(
            "auth.enabled=true; API key will be loaded from env var '%s' and optional env_file=%s.",
            cfg.auth.env_var_name,
            cfg.auth.env_file,
        )

def validate_comtrade_config(cfg: ComtradeConfig) -> None:
    

    if cfg.validation.min_comtrade_year < 1962:
        raise ValueError(
        "validation.min_comtrade_year is suspiciously low. "
        f"Got {cfg.validation.min_comtrade_year}."
    )
    if cfg.validation.max_future_year_offset < 0:
        raise ValueError(
        "validation.max_future_year_offset must be >= 0."
    )

    if cfg.validation.max_expanded_years_per_job < 1:
        raise ValueError(
        "validation.max_expanded_years_per_job must be >= 1."
    )

    if not cfg.auth.enabled:
        protected_endpoints = [
            cfg.endpoint.single,
            cfg.endpoint.bulk,
            *cfg.endpoint.single_fallbacks,
        ]

        uses_comtrade_api = any(
            "comtradeapi.un.org" in str(endpoint)
            or "api.uncomtrade.org" in str(endpoint)
            for endpoint in protected_endpoints
            if endpoint
        )

        if uses_comtrade_api:
            raise ValueError(
                "auth.enabled=false, but the configured UN Comtrade API endpoint "
                "usually requires an API subscription key. Set auth.enabled=true "
                "and provide COMTRADE_API_KEY in your environment or .env file."
            )
    if not cfg.single.enabled and not cfg.bulk.enabled:
        raise ValueError(
            "Both single.enabled and bulk.enabled are false; no jobs would run."
        )

    if cfg.single.enabled and not cfg.single.jobs:
        raise ValueError(
            "single.enabled=true but no single jobs are configured."
        )

    if cfg.bulk.enabled and not cfg.bulk.jobs:
        raise ValueError(
            "bulk.enabled=true but no bulk jobs are configured."
        )

    if cfg.single.enabled and not cfg.endpoint.single:
        raise ValueError(
            "single.enabled=true but endpoint.single is missing."
        )

    if cfg.bulk.enabled and not cfg.endpoint.bulk:
        raise ValueError(
            "bulk.enabled=true but endpoint.bulk is missing."
        )

    if cfg.runtime.max_workers < 1:
        raise ValueError(
            f"runtime.max_workers must be >= 1, got {cfg.runtime.max_workers}."
        )

    if cfg.runtime.timeout_seconds <= 0:
        raise ValueError(
            f"runtime.timeout_seconds must be > 0, got {cfg.runtime.timeout_seconds}."
        )

    if cfg.retry.max_attempts < 1:
        raise ValueError(
            f"retry.max_attempts must be >= 1, got {cfg.retry.max_attempts}."
        )

    valid_existing_file_policies = {"skip", "redownload", "fail", "warn"}

    if cfg.runtime.existing_file_policy not in valid_existing_file_policies:
        raise ValueError(
            "runtime.existing_file_policy must be one of "
            f"{sorted(valid_existing_file_policies)}, got "
            f"{cfg.runtime.existing_file_policy!r}."
        )