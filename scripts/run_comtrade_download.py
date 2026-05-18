"""
scripts/run_comtrade_download.py

Run the Comtrade download pipeline.
"""

from __future__ import annotations

from comtrade_ingest.comtrade.pipeline import run_comtrade_download_pipeline
from comtrade_ingest.io.paths import get_project_root


def main() -> None:
    config_path = get_project_root() / "configs" / "comtrade.yaml"

    try:
        run_comtrade_download_pipeline(
            config_path=config_path,
            confirm=True,
        )
    except Exception as exc:
        print("")
        print("ERROR: Comtrade download pipeline failed.")
        print(f"Reason: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()