from comtrade_ingest.comtrade.config import (
    AuthConfig,
    ComtradeConfig,
    EndpointConfig,
    ModeConfig,
    OutputConfig,
)
from comtrade_ingest.comtrade.api import (
    DownloadRuntimeConfig,
    PaginationConfig,
    RetryConfig,
)
from comtrade_ingest.io.paths import ensure_comtrade_runtime_directories


def test_ensure_comtrade_runtime_directories_creates_expected_dirs(tmp_path):
    cfg = ComtradeConfig(
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
        paths={
            "root_dir": str(tmp_path),
            "data_dir": str(tmp_path / "data"),
            "single_data_dir": str(tmp_path / "data" / "single"),
            "bulk_data_dir": str(tmp_path / "data" / "bulk"),
            "output_dir": str(tmp_path / "output"),
            "logs_dir": str(tmp_path / "output" / "logs"),
            "manifest_dir": str(tmp_path / "output" / "manifest"),
            "reports_dir": str(tmp_path / "output" / "reports"),
            "quarantine_file": str(tmp_path / "output" / "reports" / "_quarantine" / "single.json"),
        },
    )

    ensure_comtrade_runtime_directories(cfg)

    assert (tmp_path / "data" / "single").is_dir()
    assert (tmp_path / "data" / "bulk").is_dir()
    assert (tmp_path / "output" / "manifest").is_dir()
    assert (tmp_path / "output" / "logs").is_dir()
    assert (tmp_path / "output" / "reports" / "_quarantine").is_dir()