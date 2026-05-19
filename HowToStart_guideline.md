## Getting Started

This guide explains how to download, install, and run `comtrade-ingest` from GitHub.

You do not need to be an expert in Git or Python packaging. Follow the steps below carefully.

---

## 1. Install the required software

Before using this package, make sure you have:

- Python 3.11 or newer
- Git
- A terminal or command line
- A UN Comtrade API key

Check Python:

```bash
python --version
```

or:

```bash
python3 --version
```

Check Git:

```bash
git --version
```

If these commands do not work, install Python and Git first.

## 2. Download the project from GitHub

Choose a folder where you want to keep the project, then run:

```bash
git clone https://github.com/TI-ForestProductsMarkets/comtrade-ingest.git
```

Then enter the project folder:

```bash
cd comtrade-ingest
```

## 3. Create a virtual environment

A virtual environment keeps the package dependencies separate from the rest of your system.

Create the environment:

```bash
python -m venv .venv
```

Activate it.

On Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

After activation, your terminal should show something like:

```text
(.venv)
```

## 4. Install the package

Install the package in editable mode:

```bash
pip install -e .
```

For development, including testing tools, install:

```bash
pip install -e ".[dev]"
```

Editable mode means that if you change the source code, Python will use your latest local version automatically.

## 5. Add your UN Comtrade API key

The downloader needs a UN Comtrade API key.

Create a file called `.env` in the project root:

```bash
touch .env
```

Open the file and add:

```text
COMTRADE_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your real API key.

The `.env` file should not be committed to GitHub.

## 6. Edit the configuration file

The main configuration file is:

```text
configs/comtrade.yaml
```

This file controls:

- where downloaded data are saved
- whether single API mode is enabled
- whether bulk mode is enabled
- which commodity codes are downloaded
- which years are downloaded
- where logs and manifests are written

Example single-mode year configuration:

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
      use_reference_years: false
      fallback_years_start: 2020
      fallback_years_end: 2021
```

If `use_reference_years: true`, the package uses year ranges defined in the reference files.

If `use_reference_years: false`, the package uses:

- `fallback_years_start`
- `fallback_years_end`

Example bulk-mode year configuration:

```yaml
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
        enabled: true
        start: 2024
        end: 2025

      output_file: "Comtrade_bulk_HS_{period}_all_reporters.zip"
```

If the output file contains `{period}`, year expansion must be enabled.

## 7. Run the downloader

Once the package is installed and the configuration is ready, run:

```bash
comtrade-ingest run
```

The program will:

- load the configuration
- validate authentication
- run bulk downloads if enabled
- run single API downloads if enabled
- write manifests
- audit downloaded files

Logs, manifests, and reports are written to the output directories defined in `configs/comtrade.yaml`.


## 8. Common problems

### `comtrade-ingest: command not found`

The package may not be installed, or the virtual environment may not be activated.

Activate the virtual environment again:

```bash
source .venv/bin/activate
```

Then reinstall:

```bash
pip install -e .
```

### Missing API key

If you see an authentication error, check that your `.env` file contains:

```text
COMTRADE_API_KEY=your_api_key_here
```

Also check that the config has authentication enabled.

### Bulk job says `{period}` is missing

If your bulk output file contains `{period}`:

```yaml
output_file: "Comtrade_bulk_HS_{period}_all_reporters.zip"
```

then the bulk job must have years enabled:

```yaml
years:
  enabled: true
  start: 2024
  end: 2025
```

### Single job requires fallback years

If single mode has:

```yaml
use_reference_years: false
```

then you must provide:

```yaml
fallback_years_start: 2020
fallback_years_end: 2021
```

## 10. Update the package later

To get the latest version from GitHub:

```bash
git pull
```

Then reinstall if dependencies or package metadata changed:

```bash
pip install -e ".[dev]"
```
