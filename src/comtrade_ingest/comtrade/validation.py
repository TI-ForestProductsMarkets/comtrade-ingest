"""
Shared utility functions for Comtrade download modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comtrade_ingest.comtrade.config import ComtradeConfig

from comtrade_ingest.utils.logger import get_logger

logger = get_logger("COMTRADE.VALIDATION")

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