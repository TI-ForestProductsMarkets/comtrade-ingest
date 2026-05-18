from __future__ import annotations

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_project_root() -> Path:
    return PROJECT_ROOT


def make_timestamped_path(path: str | Path | None, run_id: str) -> Path | None:
    if not path:
        return None

    p = Path(path).expanduser()
    suffix = p.suffix or ".json"

    if p.suffix:
        return p.with_name(f"{p.stem}_{run_id}{p.suffix}")

    return p.with_name(f"{p.name}_{run_id}{suffix}")

def make_latest_path(path: str | Path | None) -> Path | None:
    if not path:
        return None

    p = Path(path).expanduser()
    suffix = p.suffix or ".json"

    if p.suffix:
        return p.with_name(f"{p.stem}_latest{p.suffix}")

    return p.with_name(f"{p.name}_latest{suffix}")

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


def ensure_comtrade_runtime_directories(cfg: ComtradeConfig) -> None:
    ensure_directory(cfg.single.output.directory)
    ensure_directory(cfg.bulk.output.directory)

    ensure_parent_directory(cfg.single.output.manifest_file)
    ensure_parent_directory(cfg.bulk.output.manifest_file)

    ensure_parent_directory(cfg.single.output.quarantine_file)
    ensure_parent_directory(cfg.bulk.output.quarantine_file)

    ensure_parent_directory(cfg.log_file)