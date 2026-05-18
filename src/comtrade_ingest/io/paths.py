from __future__ import annotations

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_project_root() -> Path:
    return PROJECT_ROOT


def resolve_path(path: str | Path) -> Path:
    """
    Resolve a path safely.

    Absolute paths stay absolute.
    Relative paths are resolved relative to the project root.
    """
    p = Path(path).expanduser()

    if p.is_absolute():
        return p

    return PROJECT_ROOT / p


def ensure_directory(path: str | Path | None) -> None:
    if path is None:
        return

    p = resolve_path(path)

    if p.exists() and not p.is_dir():
        raise NotADirectoryError(f"Expected directory path but found file: {p}")

    p.mkdir(parents=True, exist_ok=True)


def ensure_parent_directory(path: str | Path | None) -> None:
    if path is None:
        return

    p = resolve_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)


def ensure_comtrade_runtime_directories(cfg: Any) -> None:
    """
    Create all runtime directories needed by the Comtrade pipeline.

    Works with your ComtradeConfig dataclass.
    """
    ensure_directory(cfg.single.output.directory)
    ensure_directory(cfg.bulk.output.directory)

    ensure_directory(cfg.single.output.quarantine_directory)
    ensure_directory(cfg.bulk.output.quarantine_directory)

    ensure_parent_directory(cfg.single.output.manifest_file)
    ensure_parent_directory(cfg.bulk.output.manifest_file)

    ensure_parent_directory(cfg.log_file)