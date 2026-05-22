"""
Shared utility functions for Comtrade download modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comtrade_ingest.config.config import ComtradeConfig

from comtrade_ingest.utils.logger import get_logger

logger = get_logger("COMTRADE.VALIDATION")

def validate_job_year_source(
    *,
    section_name: str,
    idx: int,
    job_name: str,
    output_file: str,
    all_years_start: int | None,
    all_years_end: int | None,
    use_reference_years: bool,
    fallback_years_start: int | None,
    fallback_years_end: int | None,
) -> None:
    has_explicit_years = all_years_start is not None or all_years_end is not None
    has_fallback_years = (
        fallback_years_start is not None or fallback_years_end is not None
    )
    output_requires_period = "{period}" in output_file

    if section_name == "single":
        if has_explicit_years and use_reference_years:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} cannot use both "
                "years.start/end and use_reference_years=true."
            )

        if has_explicit_years and has_fallback_years:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} cannot use both "
                "years.start/end and fallback_years_start/end."
            )

        if not has_explicit_years and not use_reference_years:
            if fallback_years_start is None or fallback_years_end is None:
                raise ValueError(
                    f"{section_name}.jobs[{idx}] {job_name!r} has "
                    "use_reference_years=false, so fallback_years_start and "
                    "fallback_years_end are required."
                )

    elif section_name == "bulk":
        if use_reference_years:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} cannot use "
                "use_reference_years. Bulk jobs should use years.start/end."
            )

        if has_fallback_years:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} cannot use "
                "fallback_years_start/end. Bulk jobs should use years.start/end."
            )

        if output_requires_period and not has_explicit_years:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} has output_file "
                "containing {period}, but no years.start/end were provided."
            )

    else:
        raise ValueError(f"Unknown job section: {section_name!r}")

    
def validate_fallback_years_for_job(
    *,
    section_name: str,
    idx: int,
    job_name: str,
    use_reference_years: bool,
    years_enabled: bool,
    fallback_years_start: int | None,
    fallback_years_end: int | None,
) -> None:
    if fallback_years_start is None and fallback_years_end is not None:
        raise ValueError(
            f"{section_name}.jobs[{idx}] {job_name!r} has fallback_years_end "
            "but no fallback_years_start. Please provide both."
        )

    if fallback_years_start is not None and fallback_years_end is None:
        raise ValueError(
            f"{section_name}.jobs[{idx}] {job_name!r} has fallback_years_start "
            "but no fallback_years_end. Please provide both."
        )

    if fallback_years_start is not None and fallback_years_end is not None:
        if fallback_years_start > fallback_years_end:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} has invalid fallback years: "
                f"fallback_years_start={fallback_years_start} is greater than "
                f"fallback_years_end={fallback_years_end}."
            )

    if not use_reference_years and not years_enabled:
        if fallback_years_start is None or fallback_years_end is None:
            raise ValueError(
                f"{section_name}.jobs[{idx}] {job_name!r} has use_reference_years=false, "
                "so fallback_years_start and fallback_years_end are required.\n\n"
                "Example:\n"
                "  use_reference_years: false\n"
                "  fallback_years_start: 2020\n"
                "  fallback_years_end: 2021"
            )

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