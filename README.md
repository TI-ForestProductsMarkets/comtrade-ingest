# comtrade-ingest

`comtrade-ingest` is a config-driven downloader for UN Comtrade data.

It supports two download modes:

- **Single Data API downloads** for precise queries, such as one commodity group across one or more years.
- **Bulk API downloads** for broad annual Comtrade files, where filtering can be applied locally after download.

The package is designed around a YAML config file. Users define paths, API settings, jobs, retries, logging, and runtime behavior in `configs/comtrade.yaml`, then run one script.

For a beginner-friendly setup guide, see [Getting Started](docs/getting-started.md).

---

## Main idea

The workflow is:

```text
configs/comtrade.yaml
        ↓
resolve path templates and reference tokens
        ↓
expand jobs
        ↓
run single and/or bulk downloads
        ↓
write data files
        ↓
write manifest, logs, and reports
        ↓
audit outputs
```

For example, a user can define:

```yaml
cmdCode: "WOOD_PANEL"
flowCode: "FLOW_ALL"
use_reference_years: true
```

and the package resolves those tokens from the reference modules, expands the jobs, downloads the data, and writes manifests and logs automatically.

---

## Package structure

```text
comtrade-ingest/
├── configs/
│   └── comtrade.yaml
├── scripts/
│   └── run_comtrade_download.py
├── src/
│   └── comtrade_ingest/
│       ├── comtrade/
│       │   ├── api.py
│       │   ├── config.py
│       │   ├── download.py
│       │   ├── manifest.py
│       │   └── pipeline.py
│       ├── io/
│       │   └── paths.py
│       ├── reference/
│       │   ├── flow_sets.py
│       │   ├── hs_sets.py
│       │   └── hs_version_set.py
│       └── utils/
│           ├── logger.py
│           ├── progress.py
│           └── timing.py
└── tests/
```

Important distinction:

- Repository name: `comtrade-ingest`
- Python import package: `comtrade_ingest`

So the package is installed as `comtrade-ingest`, but imported as:

```python
import comtrade_ingest
```

---

## Installation

From the repository root:

```bash
python -m venv ../venv/comtrade-ingest
source ../venv/comtrade-ingest/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
```

Check that the package imports correctly:

```bash
python -c "import comtrade_ingest; print(comtrade_ingest)"
```

---

## Authentication

UN Comtrade API requests usually require an API subscription key.

Create a `.env` file in the project root with following content:

```text
COMTRADE_API_KEY=your_key_here
```

The default config reads this key from `.env`:

```yaml
auth:
        enabled: true
        method: "header"
        header_name: "Ocp-Apim-Subscription-Key"
        env_var_name: "COMTRADE_API_KEY"
        query_param_name: "token"
        env_file: ".env"
```

If authentication is disabled while using the standard UN Comtrade API endpoint, the pipeline fails early with a config validation error.

---

## Configuration

The main config file is:

```text
configs/comtrade.yaml
```

Usually, the first thing a new user should change is only this:

```yaml
paths:
        root_dir: "/storage/test"
```

All other paths are derived automatically:

```yaml
paths:
        root_dir: "/storage/test"

        data_dir: "{root_dir}/data"
        single_data_dir: "{data_dir}/single"
        bulk_data_dir: "{data_dir}/bulk"

        output_dir: "{root_dir}/output"
        logs_dir: "{output_dir}/logs"
        manifest_dir: "{output_dir}/manifest"
        reports_dir: "{output_dir}/reports"
        quarantine_dir: "{reports_dir}/_quarantine"
```

This produces an output layout like:

```text
/storage/test/
├── data/
│   ├── single/
│   └── bulk/
└── output/
      ├── logs/
      ├── manifest/
      └───reports/
         └── _quarantine/
```

The package creates required directories automatically.

---

## Running the pipeline

The recommended way during development is:

```bash
python scripts/run_comtrade_download.py
```

The script is intentionally minimal. It calls the package pipeline:

```python
run_comtrade_download_pipeline(...)
```

The pipeline handles:

- config loading
- path resolution
- logging setup
- runtime directory creation
- config validation
- authentication preflight
- single and bulk downloads
- manifest writing
- manifest auditing
- quarantine handling

Before downloads begin, the pipeline prints a run summary and asks for confirmation:

```text
COMTRADE_INGEST DOWNLOAD PIPELINE
========================================================================
Config file:        configs/comtrade.yaml
Runtime root-dir:   /storage/test
Log file:           /storage/test/output/logs/LOG_API_PIPELINE_YYYYMMDD_HHMMSS.log
Log level:          DEBUG

Modes:
        Bulk enabled:     no
        Single enabled:   yes

Runtime:
        max_workers:      8
        timeout_seconds:  300
        overwrite:        no

Single API:
        endpoint:         https://comtradeapi.un.org/data/v1/get/C/A/HS
        output directory: /storage/test/data/single
        manifest file:    /storage/test/output/manifest/download_manifest_single.json
        jobs:             1
        expanded jobs:    5
========================================================================
Proceed with this Comtrade download configuration? [y/N]:
```

Enter `y` to continue.

---

## Single Data API downloads

Single mode is for targeted API queries.

Example:

```yaml
single:
        enabled: true

        jobs:
                - name: "wood_panel_direct"
                        params:
                                reporterCode:
                                partnerCode:
                                cmdCode: "WOOD_PANEL"
                                flowCode: "FLOW_ALL"

                        output_file: "comtrade_{cmdCode}_{period}.csv"
                        use_reference_years: true
                        fallback_years_start: 1989
                        fallback_years_end: 2025

        output:
                directory: "{single_data_dir}"
                quarantine_file: "{quarantine_dir}/quarantine_zero_byte_single.json"
                manifest_file: "{manifest_dir}/download_manifest_single.json"
```

The package can resolve tokens such as:

```yaml
cmdCode: "WOOD_PANEL"
flowCode: "FLOW_ALL"
```

from:

- `src/comtrade_ingest/reference/hs_sets.py`
- `src/comtrade_ingest/reference/flow_sets.py`

If `use_reference_years: true`, the package uses HS reference information to expand the job across valid years for the commodity code.

Output files are written with predictable names:

```text
/storage/test/data/single/comtrade_440112_2017.csv
/storage/test/data/single/comtrade_440112_2018.csv
```

Downloaded data files are not timestamped. This keeps reruns and existing-file checks predictable.

---

## Bulk API downloads

Bulk mode is for broad annual Comtrade downloads.

Example:

```yaml
bulk:
        enabled: false

        jobs:
                - name: "hs_all_reporters"
                        params:
                                typeCode: "C"
                                freqCode: "A"
                                clCode: "HS"
                                reporterCode: "all"
                                partnerCode: "all"

                        years:
                                enabled: true
                                start: 2024
                                end: 2025

                        output_file: "Comtrade_bulk_HS_{period}_all_reporters.zip"

        output:
                directory: "{bulk_data_dir}"
                quarantine_file: "{quarantine_dir}/quarantine_zero_byte_bulk.json"
                manifest_file: "{manifest_dir}/download_manifest_bulk.json"
```

Bulk downloads are usually broad files. Commodity and flow filters should generally be applied locally after download.

---

## Logs, manifests, and run IDs

Each pipeline run gets one shared run ID:

```text
YYYYMMDD_HHMMSS
```

The run ID is used for logs and manifests.

Example:

```text
output/
├── logs/
│   └── LOG_API_PIPELINE_20260518_131430.log
├── manifest/
│   ├── download_manifest_single_20260518_131430.json
│   ├── download_manifest_single_20260518_131430_errors.csv
│   └── download_manifest_single_latest.json
└── reports/
                └── _quarantine/
```

The timestamped manifest preserves the exact run history.

The `_latest` manifest is overwritten each run for convenience.

---

## Manifest audit

After downloads finish, the pipeline audits the manifest.

The audit reports:

- total manifest rows
- downloaded jobs
- skipped jobs
- no-data jobs
- error jobs
- output file count
- existing file count
- missing file count
- zero-byte file count
- suspicious zero-byte file count
- total output size
- suffix distribution
- overall ok status

Example:

```text
Manifest audit: /storage/test/output/manifest/download_manifest_single_20260518_131430.json
        total manifest rows: 10
        downloaded jobs: 0
        status_counts: {'error': 3, 'invalid_existing': 1, 'no_data': 5, 'skipped_existing': 1}
        error jobs: 3
        output_file_count: 5
        existing_file_count: 2
        missing_file_count: 3
        zero_byte_file_count: 1
        ok: False
```

If jobs fail, an error CSV is exported:

```text
output/manifest/download_manifest_single_20260518_131430_errors.csv
```

---

## Quarantine behavior

Quarantine is for invalid local output files, such as zero-byte files.

It is not used for API errors such as rate limits or authentication failures.

For example:

```text
status = error
error_type = rate_limit
```

goes to the manifest and error CSV.

But:

```text
status = invalid_existing
validation_reason = zero_byte
```

can be quarantined.

Quarantined files are moved under:

```text
output/reports/_quarantine/
```

After quarantine, rerun the pipeline to re-download those files.

---

## Existing output files

Controlled by:

```yaml
runtime:
        overwrite_existing: false
        existing_file_policy: "redownload"
```

If `overwrite_existing: false`, valid existing files are skipped.

Valid values for `existing_file_policy`:

- `skip`
- `redownload`
- `fail`
- `warn`

Recommended default:

```yaml
existing_file_policy: "redownload"
```

---

## Retry and rate limits

Retry settings:

```yaml
retry:
        max_attempts: 3
        backoff_seconds: 2.0
        rate_limit:
                max_attempts: 5
                buffer_seconds: 5
                fallback_wait_seconds: 60
```

Meaning:

- `max_attempts`: retries for ordinary transient HTTP or network errors.
- `backoff_seconds`: base wait between retries.
- `rate_limit.max_attempts`: retries for HTTP 429 rate limits.
- `rate_limit.buffer_seconds`: extra wait added to server-provided retry time.
- `rate_limit.fallback_wait_seconds`: wait time if the server does not provide a retry time.

If `rate_limit.max_attempts: 0`, HTTP 429 retries are disabled.

---

## Running tests

Run all unit tests:

```bash
pytest -q
```

List all discovered tests:

```bash
pytest --collect-only -q
```

Run one test file:

```bash
pytest tests/test_config.py -q
```

The test suite covers:

- config loading
- strict boolean parsing
- job expansion
- path resolution
- API helper functions
- manifest auditing
- existing-file handling
- quarantine behavior
- pipeline expansion behavior

---

## Development notes

Useful commands:

```bash
tree -I "__pycache__|*.pyc|*.egg-info|.pytest_cache"
grep -R "vacoda" -n src tests scripts configs
pytest -q
python scripts/run_comtrade_download.py
```

Before committing:

```bash
pytest -q
git status
```

---

## Current scope

`comtrade-ingest` focuses on downloading and staging raw Comtrade data.

It does not aim to handle:

- HS harmonization
- data cleaning
- economic modeling
- downstream analysis
- FOB/CIF adjustments

Those should live in downstream packages or analysis projects.

