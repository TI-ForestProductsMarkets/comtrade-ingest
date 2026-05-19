from comtrade_ingest.comtrade.config import load_comtrade_config

import pytest

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
from comtrade_ingest.comtrade.utils import validate_comtrade_config


def test_validate_config_rejects_disabled_auth_for_comtrade_endpoint(tmp_path):
    cfg = ComtradeConfig(
        endpoint=EndpointConfig(
            single="https://comtradeapi.un.org/data/v1/get/C/A/HS",
            single_fallbacks=["https://api.uncomtrade.org/data/v1/get/C/A/HS"],
            bulk="https://comtradeapi.un.org/bulk/v1/get/",
        ),
        default_params={},
        single=ModeConfig(
            enabled=True,
            jobs=[object()],  # or use a real JobConfig if your type checker complains
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
            env_file=".env",
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
    )

    with pytest.raises(ValueError, match="auth.enabled=false"):
        validate_comtrade_config(cfg)

def test_config_does_not_resolve_job_output_file_templates(tmp_path):
    config_path = tmp_path / "comtrade.yaml"
    root_dir = tmp_path / "runtime"

    config_path.write_text(
        f"""
paths:
  root_dir: "{root_dir}"
  data_dir: "{{root_dir}}/data"
  single_data_dir: "{{data_dir}}/single"
  output_dir: "{{root_dir}}/output"
  logs_dir: "{{output_dir}}/logs"
  manifest_dir: "{{output_dir}}/manifest"
  quarantine_dir: "{{output_dir}}/_quarantine_zero_byte"

single:
  enabled: true
  jobs:
    - name: "test_single"
      params:
        cmdCode: "441012"
      output_file: "comtrade_{{cmdCode}}_{{period}}.csv"
      years:
        enabled: true
        start: 2020
        end: 2020
  output:
    directory: "{{single_data_dir}}"
    quarantine_file: "{{quarantine_dir}}"
    manifest_file: "{{manifest_dir}}/download_manifest_single.json"

bulk:
  enabled: false
  jobs: []
  output:
    directory: "{{root_dir}}/data/bulk"
    quarantine_file: "{{quarantine_dir}}"
    manifest_file: "{{manifest_dir}}/download_manifest_bulk.json"

log_level: INFO
log_file: "{{logs_dir}}/LOG_API_PIPELINE.log"

endpoint:
  single: "https://example.com/single"
  single_fallbacks: []
  bulk: "https://example.com/bulk"

default_params:
  format: "csv"
  maxRecords: 250000

retry:
  max_attempts: 3
  backoff_seconds: 2.0

runtime:
  timeout_seconds: 30
  overwrite_existing: false
  max_workers: 1
  existing_file_policy: "redownload"
  show_progress: false

auth:
  enabled: false
  method: "header"
  header_name: "Ocp-Apim-Subscription-Key"
  env_var_name: "COMTRADE_API_KEY"
  query_param_name: "token"
  env_file:

pagination:
  enabled: true
  limit_param: "maxRecords"
  offset_param: "offset"
  start_offset: 0
""",
        encoding="utf-8",
    )

    cfg = load_comtrade_config(config_path)

    assert cfg.single.jobs[0].output_file == "comtrade_{cmdCode}_{period}.csv"
    
def test_config_resolves_root_dir_path_templates(tmp_path):
    config_path = tmp_path / "comtrade.yaml"
    root_dir = tmp_path / "runtime"

    config_path.write_text(
        f"""
paths:
  root_dir: "{root_dir}"
  data_dir: "{{root_dir}}/data"
  single_data_dir: "{{data_dir}}/single"
  bulk_data_dir: "{{data_dir}}/bulk"
  output_dir: "{{root_dir}}/output"
  logs_dir: "{{output_dir}}/logs"
  manifest_dir: "{{output_dir}}/manifest"
  reports_dir: "{{output_dir}}/reports"
  quarantine_dir: "{{reports_dir}}/_quarantine_zero_byte"

single:
  enabled: true
  jobs:
    - name: "test_single"
      params:
        cmdCode: "441012"
      output_file: "comtrade_{{cmdCode}}_{{period}}.csv"
      years:
        enabled: true
        start: 2020
        end: 2020
  output:
    directory: "{{single_data_dir}}"
    quarantine_file: "{{quarantine_dir}}"
    manifest_file: "{{manifest_dir}}/download_manifest_single.json"

bulk:
  enabled: false
  jobs: []
  output:
    directory: "{{bulk_data_dir}}"
    quarantine_file: "{{quarantine_dir}}"
    manifest_file: "{{manifest_dir}}/download_manifest_bulk.json"

log_level: INFO
log_file: "{{logs_dir}}/LOG_API_PIPELINE.log"

endpoint:
  single: "https://example.com/single"
  single_fallbacks: []
  bulk: "https://example.com/bulk"

default_params:
  format: "csv"
  maxRecords: 250000

retry:
  max_attempts: 3
  backoff_seconds: 2.0

runtime:
  timeout_seconds: 30
  overwrite_existing: false
  max_workers: 1
  existing_file_policy: "redownload"
  show_progress: false

auth:
  enabled: false
  method: "header"
  header_name: "Ocp-Apim-Subscription-Key"
  env_var_name: "COMTRADE_API_KEY"
  query_param_name: "token"
  env_file:

pagination:
  enabled: true
  limit_param: "maxRecords"
  offset_param: "offset"
  start_offset: 0
""",
        encoding="utf-8",
    )

    cfg = load_comtrade_config(config_path)

    assert cfg.single.output.directory == str(root_dir / "data" / "single")
    assert cfg.bulk.output.directory == str(root_dir / "data" / "bulk")
    assert cfg.single.output.manifest_file == str(
        root_dir / "output" / "manifest" / "download_manifest_single.json"
    )
    assert cfg.single.output.quarantine_file == str(
        root_dir / "output" / "reports" / "_quarantine_zero_byte"
    )
    assert cfg.log_file == str(root_dir / "output" / "logs" / "LOG_API_PIPELINE.log")

def test_load_config_explicit_years(tmp_path):
    config_path = tmp_path / "comtrade.yaml"
    config_path.write_text(
        """
bulk:
  enabled: true
  jobs:
    - name: "hs_all_reporters"
      params:
        typeCode: "C"
        freqCode: "A"
        clCode: "HS"
      years:
        enabled: true
        start: 2024
        end: 2025
      output_file: "Comtrade_bulk_HS_{period}.zip"
  output:
    directory: "data/raw/api/bulk"
    manifest_file: "download_manifest_bulk.json"

single:
  enabled: false
  jobs: []
  output:
    directory: "data/raw/api/single"
    manifest_file: "download_manifest_single.json"

endpoint:
  single: "https://example.com/single"
  single_fallbacks: []
  bulk: "https://example.com/bulk"

default_params:
  format: "csv"

retry:
  max_attempts: 3
  backoff_seconds: 2.0

runtime:
  timeout_seconds: 300
  overwrite_existing: false
  existing_file_policy: "redownload"
  max_workers: 8

auth:
  enabled: false

pagination:
  enabled: true
""",
        encoding="utf-8",
    )

    cfg = load_comtrade_config(config_path)

    job = cfg.bulk.jobs[0]
    assert job.all_years_start == 2024
    assert job.all_years_end == 2025
    assert job.use_reference_years is False

def test_load_config_reference_years(tmp_path):
    config_path = tmp_path / "comtrade.yaml"
    config_path.write_text(
        """
bulk:
  enabled: false
  jobs: []
  output:
    directory: "data/raw/api/bulk"
    manifest_file: "download_manifest_bulk.json"

single:
  enabled: true
  jobs:
    - name: "wood_panel_direct"
      params:
        cmdCode: "441012"
      output_file: "comtrade_{cmdCode}_{period}.csv"
      use_reference_years: true
      fallback_years_start: 1989
      fallback_years_end: 2025
  output:
    directory: "data/raw/api/single"
    manifest_file: "download_manifest_single.json"

endpoint:
  single: "https://example.com/single"
  single_fallbacks: []
  bulk: "https://example.com/bulk"

default_params:
  format: "csv"

retry:
  max_attempts: 3
  backoff_seconds: 2.0

runtime:
  timeout_seconds: 300
  overwrite_existing: false
  existing_file_policy: "redownload"
  max_workers: 8

auth:
  enabled: false

pagination:
  enabled: true
""",
        encoding="utf-8",
    )

    cfg = load_comtrade_config(config_path)

    job = cfg.single.jobs[0]
    assert job.all_years_start is None
    assert job.all_years_end is None
    assert job.use_reference_years is True
    assert job.fallback_years_start == 1989
    assert job.fallback_years_end == 2025


def test_load_config_rejects_invalid_boolean(tmp_path):
    config_path = tmp_path / "comtrade.yaml"

    config_path.write_text(
        """
single:
  enabled: tru
  jobs: []

bulk:
  enabled: false
  jobs: []

endpoint:
  single: "https://example.com/single"
  single_fallbacks: []
  bulk: "https://example.com/bulk"

default_params: {}

retry:
  max_attempts: 3
  backoff_seconds: 2.0

runtime:
  timeout_seconds: 30
  overwrite_existing: false
  max_workers: 1
  existing_file_policy: "redownload"
  show_progress: true

auth:
  enabled: false
  method: "header"
  header_name: "Ocp-Apim-Subscription-Key"
  env_var_name: "COMTRADE_API_KEY"
  query_param_name: "token"
  env_file:

pagination:
  enabled: true
  limit_param: "maxRecords"
  offset_param: "offset"
  start_offset: 0

log_level: INFO
log_file:
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="single.enabled must be a boolean"):
        load_comtrade_config(config_path)


def test_load_config_exposes_resolved_paths(tmp_path):
    config_path = tmp_path / "comtrade.yaml"
    root_dir = tmp_path / "runtime"

    config_path.write_text(
        f"""
paths:
  root_dir: "{root_dir}"
  data_dir: "{{root_dir}}/data"
  single_data_dir: "{{data_dir}}/single"
  bulk_data_dir: "{{data_dir}}/bulk"
  output_dir: "{{root_dir}}/output"
  logs_dir: "{{output_dir}}/logs"
  manifest_dir: "{{output_dir}}/manifest"
  reports_dir: "{{output_dir}}/reports"
  quarantine_dir: "{{reports_dir}}/_quarantine_zero_byte"

single:
  enabled: false
  jobs: []
  output:
    directory: "{{single_data_dir}}"
    quarantine_file: "{{quarantine_dir}}"
    manifest_file: "{{manifest_dir}}/download_manifest_single.json"

bulk:
  enabled: false
  jobs: []
  output:
    directory: "{{bulk_data_dir}}"
    quarantine_file: "{{quarantine_dir}}"
    manifest_file: "{{manifest_dir}}/download_manifest_bulk.json"

log_level: INFO
log_file: "{{logs_dir}}/LOG_API_PIPELINE.log"

endpoint:
  single: "https://example.com/single"
  single_fallbacks: []
  bulk: "https://example.com/bulk"

default_params:
  format: "csv"
  maxRecords: 250000

retry:
  max_attempts: 3
  backoff_seconds: 2.0

runtime:
  timeout_seconds: 30
  overwrite_existing: false
  max_workers: 1
  existing_file_policy: "redownload"
  show_progress: false

auth:
  enabled: false
  method: "header"
  header_name: "Ocp-Apim-Subscription-Key"
  env_var_name: "COMTRADE_API_KEY"
  query_param_name: "token"
  env_file:

pagination:
  enabled: true
  limit_param: "maxRecords"
  offset_param: "offset"
  start_offset: 0
""",
        encoding="utf-8",
    )

    cfg = load_comtrade_config(config_path)

    assert cfg.paths["root_dir"] == str(root_dir)
    assert cfg.paths["single_data_dir"] == str(root_dir / "data" / "single")
    assert cfg.paths["logs_dir"] == str(root_dir / "output" / "logs")