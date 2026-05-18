"""
comtrade_ingest.cli

Command-line interface for comtrade-ingest.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from comtrade_ingest.comtrade.pipeline import run_comtrade_download_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="comtrade-ingest",
        description="Config-driven UN Comtrade ingestion pipeline.",
    )
    parser.add_argument(
        "command",
        choices=["run"],
        help="Command to execute.",
    )
    parser.add_argument(
        "--config",
        default="configs/comtrade.yaml",
        help="Path to the Comtrade YAML config.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run without interactive confirmation.",
    )

    args = parser.parse_args()

    if args.command == "run":
        run_comtrade_download_pipeline(
            config_path=Path(args.config),
            confirm=args.yes,
        )


if __name__ == "__main__":
    main()