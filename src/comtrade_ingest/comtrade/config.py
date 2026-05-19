from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from comtrade_ingest.comtrade.api import (
    AuthConfig,
    DownloadRuntimeConfig,
    PaginationConfig,
    RetryConfig,
)
from comtrade_ingest.comtrade.utils import load_yaml
from comtrade_ingest.reference import flow_sets, hs_sets
from comtrade_ingest.utils.logger import get_logger

logger = get_logger("COMTRADE.CONFIG")


@dataclass
class EndpointConfig:
    single: str
    single_fallbacks: list[str]
    bulk: str


@dataclass
class OutputConfig:
    directory: str
    manifest_file: str
    quarantine_file: str | None = None

@dataclass
class JobConfig:
    name: str
    params: dict[str, Any]
    output_file: str
    local_filter: dict[str, Any] | None = None
    all_years_start: int | None = None
    all_years_end: int | None = None
    use_reference_years: bool = False
    fallback_years_start: int = 1990
    fallback_years_end: int = 2025


@dataclass
class ModeConfig:
    enabled: bool
    jobs: list[JobConfig]
    output: OutputConfig

@dataclass
class ValidationConfig:
    min_comtrade_year: int = 1962
    max_future_year_offset: int = 1
    max_expanded_years_per_job: int = 200

@dataclass
class ComtradeConfig:
    endpoint: EndpointConfig
    default_params: dict[str, Any]
    single: ModeConfig
    bulk: ModeConfig
    retry: RetryConfig
    runtime: DownloadRuntimeConfig
    auth: AuthConfig
    pagination: PaginationConfig
    log_level: str
    log_file: str | None
    paths: dict[str, str]
    validation: ValidationConfig = field(default_factory=ValidationConfig)



def _resolve_path_templates(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Resolve only path-related templates.

    This intentionally does NOT resolve every string in the config,
    because fields like output_file use job templates such as:

        comtrade_{cmdCode}_{period}.csv

    Those must be resolved later during job expansion.
    """
    paths_cfg = raw.get("paths", {})

    if paths_cfg is None:
        paths_cfg = {}

    if not isinstance(paths_cfg, dict):
        raise ValueError("paths must be a mapping")

    resolved_paths: dict[str, str] = {}

    for key, value in paths_cfg.items():
        if value is None:
            continue

        if not isinstance(value, str):
            raise ValueError(
                f"paths.{key} must be a string, got {type(value).__name__}"
            )

        try:
            resolved_paths[key] = value.format(**resolved_paths)
        except KeyError as exc:
            missing = exc.args[0]
            raise KeyError(
                f"paths.{key} references unknown path template {{{missing}}}"
            ) from exc

    raw["paths"] = resolved_paths

    def resolve_path_value(value: Any, field_name: str) -> Any:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        try:
            return value.format(**resolved_paths)
        except KeyError as exc:
            missing = exc.args[0]
            raise KeyError(
                f"{field_name} references unknown path template {{{missing}}}"
            ) from exc

    # Top-level log file
    raw["log_file"] = resolve_path_value(raw.get("log_file"), "log_file")

    # Mode-specific output paths
    for mode_name in ["single", "bulk"]:
        mode_cfg = raw.get(mode_name, {})

        if not isinstance(mode_cfg, dict):
            continue

        output_cfg = mode_cfg.get("output", {})

        if not isinstance(output_cfg, dict):
            continue

        for field_name in ["directory", "manifest_file", "quarantine_file"]:
            if field_name in output_cfg:
                output_cfg[field_name] = resolve_path_value(
                    output_cfg[field_name],
                    f"{mode_name}.output.{field_name}",
                )

    return raw



def _resolve_reference_token(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    token = value.strip()
    if not token:
        return value

    resolved = getattr(hs_sets, token, None)

    if resolved is None:
        resolved = getattr(flow_sets, token, None)

    if resolved is None:
        return value

    if isinstance(resolved, tuple):
        return list(resolved)

    return resolved


def _resolve_params(params: dict[str, Any]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}

    for key, value in params.items():
        resolved[key] = _resolve_reference_token(value)

    return resolved

def _validate_fallback_years_for_job(
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


def _load_jobs(section_name: str, section_cfg: dict[str, Any]) -> list[JobConfig]:
    raw_jobs = section_cfg.get("jobs", [])

    if not isinstance(raw_jobs, list):
        raise ValueError(f"{section_name}.jobs must be a list")

    jobs: list[JobConfig] = []

    for idx, raw_job in enumerate(raw_jobs):
        if not isinstance(raw_job, dict):
            raise ValueError(f"{section_name}.jobs[{idx}] must be a mapping")

        name = str(raw_job.get("name", "")).strip()
        if not name:
            raise ValueError(f"{section_name}.jobs[{idx}].name is required")

        params = raw_job.get("params", {})
        if not isinstance(params, dict):
            raise ValueError(f"{section_name}.jobs[{idx}].params must be a mapping")

        output_file = str(raw_job.get("output_file", "")).strip()
        if not output_file:
            raise ValueError(f"{section_name}.jobs[{idx}].output_file is required")

        local_filter = raw_job.get("local_filter")
        if local_filter is not None and not isinstance(local_filter, dict):
            raise ValueError(f"{section_name}.jobs[{idx}].local_filter must be a mapping")

        years_cfg = raw_job.get("years", {})
        if years_cfg is None:
            years_cfg = {}
        if not isinstance(years_cfg, dict):
            raise ValueError(f"{section_name}.jobs[{idx}].years must be a mapping")

        years_enabled = _parse_bool(
                        years_cfg.get("enabled", False),
                        field_name=f"{section_name}.jobs[{idx}].years.enabled",
                        )

        use_reference_years = _parse_bool(
            raw_job.get("use_reference_years", False),
            field_name=f"{section_name}.jobs[{idx}].use_reference_years",
        )

        if years_enabled and use_reference_years:
            raise ValueError(
                f"{section_name}.jobs[{idx}] cannot use both "
                "years.enabled=true and use_reference_years=true. "
                "Use explicit years OR HS-reference-driven years, not both."
            )

        all_years_start = None
        all_years_end = None

        if years_enabled:
            if "start" not in years_cfg or "end" not in years_cfg:
                raise ValueError(
                    f"{section_name}.jobs[{idx}].years.enabled=true requires "
                    "years.start and years.end"
                )

            all_years_start = int(years_cfg["start"])
            all_years_end = int(years_cfg["end"])

            if all_years_start > all_years_end:
                raise ValueError(
                    f"{section_name}.jobs[{idx}].years.start "
                    f"({all_years_start}) is greater than years.end ({all_years_end})"
                )
        
        fallback_years_start = _parse_optional_int(raw_job.get("fallback_years_start"),
                                                    field_name=f"{section_name}.jobs[{idx}].fallback_years_start",)

        fallback_years_end = _parse_optional_int(raw_job.get("fallback_years_end"),
                                                field_name=f"{section_name}.jobs[{idx}].fallback_years_end",)

        _validate_fallback_years_for_job(
                    section_name=section_name,
                    idx=idx,
                    job_name=name,
                    use_reference_years=use_reference_years,
                    years_enabled=years_enabled,
                    fallback_years_start=fallback_years_start,
                    fallback_years_end=fallback_years_end)

        jobs.append(
            JobConfig(
                name=name,
                params=_resolve_params(params),
                output_file=output_file,
                local_filter=(
                    _resolve_params(local_filter)
                    if isinstance(local_filter, dict)
                    else None
                ),
                all_years_start=all_years_start,
                all_years_end=all_years_end,
                use_reference_years=use_reference_years,
                fallback_years_start=_parse_optional_int(
                    raw_job.get("fallback_years_start"),
                    field_name=f"{section_name}.jobs[{idx}].fallback_years_start",
                ),
                fallback_years_end=_parse_optional_int(
                    raw_job.get("fallback_years_end"),
                    field_name=f"{section_name}.jobs[{idx}].fallback_years_end",
),
            )
        )

    return jobs

def _parse_optional_int(value: Any, *, field_name: str) -> int | None:
    """
    Parse an optional integer field.

    Empty YAML values become None, and should stay None so that
    validation can produce a clear, contextual error later.
    """
    if value is None:
        return None

    if isinstance(value, str) and value.strip() == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be an integer. "
            f"Got {value!r}."
        ) from exc

def _parse_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "yes", "y", "1"}:
            return True

        if normalized in {"false", "no", "n", "0"}:
            return False

    raise ValueError(
        f"{field_name} must be a boolean. Use true/false, yes/no, or 1/0. "
        f"Got {value!r}."
    )

def _load_output(section_cfg: dict[str, Any], default_dir: str, default_manifest: str) -> OutputConfig:
    output_cfg = section_cfg.get("output", {})
    if not isinstance(output_cfg, dict):
        output_cfg = {}

    return OutputConfig(
        directory=str(output_cfg.get("directory", default_dir)),
        manifest_file=str(output_cfg.get("manifest_file", default_manifest)),
        quarantine_file=(
            str(output_cfg.get("quarantine_file"))
            if output_cfg.get("quarantine_file")
            else None
        ),
    )


def _load_mode(
    section_name: str,
    cfg: dict[str, Any],
    default_dir: str,
    default_manifest: str,
) -> ModeConfig:
    section_cfg = cfg.get(section_name, {})
    if not isinstance(section_cfg, dict):
        section_cfg = {}

    return ModeConfig(
        enabled=_parse_bool(
                    section_cfg.get("enabled", False),
                    field_name=f"{section_name}.enabled",
                    ),
        jobs=_load_jobs(section_name, section_cfg),
        output=_load_output(section_cfg, default_dir, default_manifest),
    )

def load_comtrade_config(path: Path) -> ComtradeConfig:
    raw = load_yaml(path)
    raw = _resolve_path_templates(raw)

    validation_cfg = raw.get("validation", {})
    if not isinstance(validation_cfg, dict):
        validation_cfg = {}

    endpoint_cfg = raw.get("endpoint", {})
    if not isinstance(endpoint_cfg, dict):
        raise ValueError("endpoint must be a mapping with single, single_fallbacks, bulk")

    default_params = raw.get("default_params", {})
    if not isinstance(default_params, dict):
        raise ValueError("default_params must be a mapping")

    retry_cfg = raw.get("retry", {})
    runtime_cfg = raw.get("runtime", {})
    auth_cfg = raw.get("auth", {})
    pagination_cfg = raw.get("pagination", {})

    if not isinstance(retry_cfg, dict):
        retry_cfg = {}
    if not isinstance(runtime_cfg, dict):
        runtime_cfg = {}
    if not isinstance(auth_cfg, dict):
        auth_cfg = {}
    if not isinstance(pagination_cfg, dict):
        pagination_cfg = {}

    cfg = ComtradeConfig(
        endpoint=EndpointConfig(
            single=str(endpoint_cfg.get("single", "")).strip(),
            single_fallbacks=[
                str(item).strip()
                for item in endpoint_cfg.get("single_fallbacks", [])
                if str(item).strip()
            ],
            bulk=str(endpoint_cfg.get("bulk", "")).strip(),
        ),
        default_params=default_params,
        single=_load_mode(
            "single",
            raw,
            default_dir="data/raw/api/single",
            default_manifest="download_manifest_single.json",
        ),
        bulk=_load_mode(
            "bulk",
            raw,
            default_dir="data/raw/api/bulk",
            default_manifest="download_manifest_bulk.json",
        ),
        retry=RetryConfig(
            max_attempts=int(retry_cfg.get("max_attempts", retry_cfg.get("retries", 3))),
            backoff_seconds=float(retry_cfg.get("backoff_seconds", 2.0)),
            rate_limit_max_attempts=int(retry_cfg.get("rate_limit", {}).get("max_attempts", 10)),
            rate_limit_buffer_seconds=float(retry_cfg.get("rate_limit", {}).get("buffer_seconds", 0.5)),
            rate_limit_fallback_wait_seconds=float(retry_cfg.get("rate_limit", {}).get("fallback_wait_seconds", 2.0)),
        ),
        runtime=DownloadRuntimeConfig(
            timeout_seconds=int(runtime_cfg.get("timeout_seconds", 120)),
             overwrite_existing=_parse_bool(
                            runtime_cfg.get("overwrite_existing", False),
                            field_name="runtime.overwrite_existing",
                ),
            max_workers=int(runtime_cfg.get("max_workers", 4)),
            existing_file_policy=str(runtime_cfg.get("existing_file_policy", "redownload")).strip().lower(),
            show_progress=_parse_bool(
                            runtime_cfg.get("show_progress", True),
                            field_name="runtime.show_progress",
                    ),),
        auth=AuthConfig(
            enabled=_parse_bool(
                        auth_cfg.get("enabled", False),
                        field_name="auth.enabled",
                    ),
            method=str(auth_cfg.get("method", "query")).strip().lower(),
            header_name=str(auth_cfg.get("header_name", "Ocp-Apim-Subscription-Key")),
            env_var_name=str(auth_cfg.get("env_var_name", "COMTRADE_API_KEY")),
            query_param_name=str(auth_cfg.get("query_param_name", "token")),
            env_file=(str(auth_cfg.get("env_file", "")).strip() or None),
        ),
        pagination=PaginationConfig(
            enabled=_parse_bool(pagination_cfg.get("enabled", False),
                                field_name="pagination.enabled",
                            ),
            limit_param=str(pagination_cfg.get("limit_param", "maxRecords")),
            offset_param=str(pagination_cfg.get("offset_param", "offset")),
            start_offset=int(pagination_cfg.get("start_offset", 0)),
        ),
        log_level=str(raw.get("log_level", "INFO")),
        log_file=raw.get("log_file"),
        paths=raw.get("paths", {}),
        validation=ValidationConfig(
            min_comtrade_year=int(validation_cfg.get("min_comtrade_year", 1962)),
            max_future_year_offset=int(validation_cfg.get("max_future_year_offset", 1)),
            max_expanded_years_per_job=int(
            validation_cfg.get("max_expanded_years_per_job", 200)
        ),)
    )

    if cfg.single.enabled and not cfg.endpoint.single:
        raise ValueError("single.enabled=true but endpoint.single is missing")

    if cfg.bulk.enabled and not cfg.endpoint.bulk:
        raise ValueError("bulk.enabled=true but endpoint.bulk is missing")

    return cfg