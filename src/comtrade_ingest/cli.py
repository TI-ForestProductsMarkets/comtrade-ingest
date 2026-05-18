"""
comtrade_ingest.cli

Command-line entry point for comtrade-ingest.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from comtrade_ingest.comtrade.errors import ComtradeIngestError, print_cli_error
from comtrade_ingest.comtrade.pipeline import run_comtrade_download_pipeline
from comtrade_ingest.io.paths import get_project_root


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="comtrade-ingest",
        description="Config-driven UN Comtrade download pipeline.",
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run"],
        help="Command to run. Default: run",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to comtrade.yaml. Default: configs/comtrade.yaml",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run without interactive confirmation.",
    )

    args = parser.parse_args()

    config_path = args.config or get_project_root() / "configs" / "comtrade.yaml"

    try:
        if args.command == "run":
            run_comtrade_download_pipeline(
                config_path=config_path,
                confirm=not args.yes,
            )
            
    except ComtradeIngestError as exc:
        print_cli_error(
        title="COMTRADE-INGEST PIPELINE STOPPED",
        reason=str(exc),)
        raise SystemExit(1)

    except KeyboardInterrupt:
        print("")
        print("Pipeline stopped by user.")
        raise SystemExit(130)

    except Exception as exc:
        print("")
        print("ERROR: Comtrade download pipeline failed unexpectedly.")
        print(f"Reason: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()