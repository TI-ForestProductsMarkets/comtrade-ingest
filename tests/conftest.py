"""Pytest configuration and shared test fixtures."""

from pathlib import Path
from comtrade_ingest.comtrade.config import (
    ComtradeConfig,
    EndpointConfig,
    ModeConfig,
    OutputConfig,
    ValidationConfig,
)
from comtrade_ingest.comtrade.api import (
    AuthConfig,
    DownloadRuntimeConfig,
    PaginationConfig,
    RetryConfig,
)


def create_test_config(tmp_path: Path | None = None) -> ComtradeConfig:
    """Create a minimal test ComtradeConfig with sensible defaults."""
    if tmp_path is None:
        tmp_path = Path("/tmp/test_comtrade")
    
    return ComtradeConfig(
        endpoint=EndpointConfig(
            single="https://example.com/single",
            single_fallbacks=[],
            bulk="https://example.com/bulk",
        ),
        default_params={},
        single=ModeConfig(
            enabled=True,
            jobs=[],
            output=OutputConfig(
                directory=str(tmp_path / "data" / "single"),
                manifest_file=str(tmp_path / "output" / "manifest" / "single.json"),
                quarantine_file=str(tmp_path / "output" / "reports" / "_quarantine" / "single.json"),
            ),
        ),
        bulk=ModeConfig(
            enabled=False,
            jobs=[],
            output=OutputConfig(
                directory=str(tmp_path / "data" / "bulk"),
                manifest_file=str(tmp_path / "output" / "manifest" / "bulk.json"),
                quarantine_file=str(tmp_path / "output" / "reports" / "_quarantine" / "bulk.json"),
            ),
        ),
        retry=RetryConfig(max_attempts=3, backoff_seconds=2.0),
        runtime=DownloadRuntimeConfig(
            timeout_seconds=30,
            overwrite_existing=False,
            max_workers=1,
            existing_file_policy="redownload",
            show_progress=False,
        ),
        auth=AuthConfig(
            enabled=False,
            method="header",
            header_name="Ocp-Apim-Subscription-Key",
            env_var_name="COMTRADE_API_KEY",
            query_param_name="token",
            env_file=None,
        ),
        pagination=PaginationConfig(
            enabled=True,
            limit_param="maxRecords",
            offset_param="offset",
            start_offset=0,
        ),
        log_level="INFO",
        log_file=str(tmp_path / "output" / "logs" / "LOG_API_PIPELINE.log"),
        paths={"root_dir": str(tmp_path)},
        validation=ValidationConfig(
            min_comtrade_year=1990,
            max_future_year_offset=5,
            max_expanded_years_per_job=100,
        ),
    )
