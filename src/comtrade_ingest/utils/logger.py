
import logging
from datetime import datetime
from pathlib import Path
_PROJECT_ROOT = Path(__file__).parents[3]


def rel_path(path) -> str:
    """Return path relative to project root for concise log messages."""
    try:
        return str(Path(path).relative_to(_PROJECT_ROOT))
    except ValueError:
        return str(path)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger for the given module name.

    Usage
    -----
    from comtrade_ingest.utils.logger import get_logger
    logger = get_logger(__name__)

    logger.debug("detailed info for debugging")
    logger.info("general progress message")
    logger.warning("something unexpected but not fatal")
    logger.error("something went wrong")
    """
    return logging.getLogger(name)


def setup_logging(level: int = logging.INFO, log_file: str | Path | None = None) -> None:
    """
    Configure root logging for the comtrade_ingest package with console and optional file output.
    Call this once at the entry point (script or app).

    Parameters
    ----------
    level : int
        Logging level, e.g. logging.DEBUG, logging.INFO (default).
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = _PROJECT_ROOT / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers regardless of the chosen level
    for noisy in ("watchdog", "urllib3", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)




def get_log_level(log_level: str | int | None) -> int:
    if log_level is None:
        return logging.INFO

    if isinstance(log_level, int):
        return log_level

    return getattr(logging, str(log_level).upper(), logging.INFO)

def make_run_id() -> str:
    """
    Create a timestamp-like run id shared across logs, manifests, and reports.

    Example:
        20260518_110439
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_timestamped_log_path(
    log_file: str | Path | None,
    run_id: str | None = None,
) -> Path | None:
    if not log_file:
        return None

    path = Path(log_file).expanduser()
    timestamp = run_id or make_run_id()

    return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
