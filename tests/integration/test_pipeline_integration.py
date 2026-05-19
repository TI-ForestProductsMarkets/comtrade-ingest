from pathlib import Path

import pytest

from comtrade_ingest.comtrade.errors import ConfigValidationError
from comtrade_ingest.comtrade.pipeline import run_comtrade_download_pipeline

pytestmark = pytest.mark.integration


def _base_config_yaml(root_dir: Path) -> str:
    return f"""
paths:
  root_dir: "{root_dir}"
  data_dir: "{{root_dir}}/data"
  single_data_dir: "{{data_dir}}/single"
  bulk_data_dir: "{{data_dir}}/bulk"
  output_dir: "{{root_dir}}/output"
  logs_dir: "{{output_dir}}/logs"
  manifest_dir: "{{output_dir}}/manifest"
  reports_dir: "{{output_dir}}/reports"
  quarantine_dir: "{{reports_dir}}/_quarantine"

auth:
  enabled: false

endpoint:
  single: "https://example.test/data"
  single_fallbacks: []
  bulk: "https://example.test/bulk"

default_params:
  format: "csv"
  maxRecords: 250000
  includeDesc: true

pagination:
  enabled: false

runtime:
  overwrite_existing: true
  existing_file_policy: "warn"
  max_workers: 1
  timeout_seconds: 30
  show_progress: false

retry:
  max_attempts: 1
  backoff_seconds: 0
  rate_limit_max_attempts: 1
  rate_limit_buffer_seconds: 0
  rate_limit_fallback_wait_seconds: 0

validation:
  min_comtrade_year: 1962
  max_future_year_offset: 1
  max_expanded_years_per_job: 20

log_level: INFO
log_file: "{{logs_dir}}/LOG_API_PIPELINE.log"
"""


def test_single_pipeline_writes_manifest_with_mocked_download(tmp_path, monkeypatch):
    config_path = tmp_path / "comtrade.yaml"
    root_dir = tmp_path / "runtime"

    config_path.write_text(
        _base_config_yaml(root_dir)
        + """
single:
  enabled: true
  jobs:
    - name: "wood_panel_direct"
      params:
        reporterCode:
        partnerCode:
        cmdCode: "440112"
        flowCode: "M"
      output_file: "comtrade_{cmdCode}_{period}.csv"
      use_reference_years: false
      fallback_years_start: 2020
      fallback_years_end: 2021
  output:
    directory: "{single_data_dir}"
    quarantine_file: "{quarantine_dir}/quarantine_zero_byte_single.json"
    manifest_file: "{manifest_dir}/download_manifest_single.json"

bulk:
  enabled: false
  jobs: []
  output:
    directory: "{bulk_data_dir}"
    quarantine_file: "{quarantine_dir}/quarantine_zero_byte_bulk.json"
    manifest_file: "{manifest_dir}/download_manifest_bulk.json"
""",
        encoding="utf-8",
    )

    def fake_download_with_retry(*, url, retry, runtime, headers=None):
        return b"RefYear,CmdCode,PrimaryValue\n2020,440112,100\n"

    monkeypatch.setattr(
        "comtrade_ingest.comtrade.pipeline.download_with_retry",
        fake_download_with_retry,
    )
    monkeypatch.setattr(
        "comtrade_ingest.comtrade.pipeline.validate_auth_preflight",
        lambda auth: None,
    )
    monkeypatch.setattr(
        "comtrade_ingest.comtrade.pipeline.select_resolvable_endpoint",
        lambda primary, fallbacks: primary,
    )

    rows = run_comtrade_download_pipeline(
        config_path=config_path,
        require_confirmation=False,
    )

    assert len(rows) == 2
    assert {row["status"] for row in rows} == {"downloaded"}
    assert (root_dir / "data" / "single" / "comtrade_440112_2020.csv").exists()
    assert (root_dir / "data" / "single" / "comtrade_440112_2021.csv").exists()

    latest_manifest = (
        root_dir / "output" / "manifest" / "download_manifest_single_latest.json"
    )
    assert latest_manifest.exists()


def test_bulk_pipeline_writes_manifest_with_mocked_download(tmp_path, monkeypatch):
    config_path = tmp_path / "comtrade.yaml"
    root_dir = tmp_path / "runtime"

    config_path.write_text(
        _base_config_yaml(root_dir)
        + """
single:
  enabled: false
  jobs: []
  output:
    directory: "{single_data_dir}"
    quarantine_file: "{quarantine_dir}/quarantine_zero_byte_single.json"
    manifest_file: "{manifest_dir}/download_manifest_single.json"

bulk:
  enabled: true
  jobs:
    - name: "hs_all_reporters"
      params:
        typeCode: "C"
        freqCode: "A"
        clCode: "HS"
        reporterCode: "all"
        partnerCode: "all"
      years:
        start: 2021
        end: 2022
      output_file: "Comtrade_bulk_HS_{period}_all_reporters.zip"
  output:
    directory: "{bulk_data_dir}"
    quarantine_file: "{quarantine_dir}/quarantine_zero_byte_bulk.json"
    manifest_file: "{manifest_dir}/download_manifest_bulk.json"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "comtrade_ingest.comtrade.pipeline.validate_auth_preflight",
        lambda auth: None,
    )

    def fake_download_bulk(*, endpoint, job_params, retry, runtime, auth, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake bulk data 2026")
        return [str(output_path)]

    monkeypatch.setattr(
        "comtrade_ingest.comtrade.pipeline.download_bulk",
        fake_download_bulk,
    )

    rows = run_comtrade_download_pipeline(
        config_path=config_path,
        require_confirmation=False,
    )

    assert len(rows) == 2
    assert {row["status"] for row in rows} == {"downloaded"}
    assert (
        root_dir / "data" / "bulk" / "Comtrade_bulk_HS_2021_all_reporters.zip"
    ).exists()
    assert (
        root_dir / "data" / "bulk" / "Comtrade_bulk_HS_2022_all_reporters.zip"
    ).exists()

    latest_manifest = (
        root_dir / "output" / "manifest" / "download_manifest_bulk_latest.json"
    )
    assert latest_manifest.exists()


def test_bulk_period_template_requires_years(tmp_path):
    config_path = tmp_path / "comtrade.yaml"
    root_dir = tmp_path / "runtime"

    config_path.write_text(
        _base_config_yaml(root_dir)
        + """
single:
  enabled: false
  jobs: []
  output:
    directory: "{single_data_dir}"
    quarantine_file: "{quarantine_dir}/quarantine_zero_byte_single.json"
    manifest_file: "{manifest_dir}/download_manifest_single.json"

bulk:
  enabled: true
  jobs:
    - name: "hs_all_reporters"
      params:
        typeCode: "C"
        freqCode: "A"
        clCode: "HS"
      output_file: "Comtrade_bulk_HS_{period}.zip"
  output:
    directory: "{bulk_data_dir}"
    quarantine_file: "{quarantine_dir}/quarantine_zero_byte_bulk.json"
    manifest_file: "{manifest_dir}/download_manifest_bulk.json"
""",
        encoding="utf-8",
    )

    with pytest.raises((ValueError, ConfigValidationError), match="output_file.*period"):
        run_comtrade_download_pipeline(
            config_path=config_path,
            require_confirmation=False,
        )
