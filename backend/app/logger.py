"""
Logging setup.
Every day gets its own folder:  logs/2025-01-31/info.log  and  logs/2025-01-31/error.log
"""
import logging
from datetime import date
from pathlib import Path

from app.config import settings

FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"


class DailyFileHandler(logging.Handler):
    """Appends records to logs/<today>/<filename>; a new folder starts automatically at midnight."""

    def __init__(self, filename: str, only_errors: bool):
        super().__init__()
        self.filename = filename
        self.only_errors = only_errors

    def emit(self, record):
        # error.log takes ERROR and above, info.log takes everything below that
        is_error = record.levelno >= logging.ERROR
        if is_error != self.only_errors:
            return
        try:
            folder = Path(settings.LOG_DIR) / date.today().isoformat()
            folder.mkdir(parents=True, exist_ok=True)
            with open(folder / self.filename, "a", encoding="utf-8") as f:
                f.write(self.format(record) + "\n")
        except Exception:
            # logging must never crash the app
            self.handleError(record)


def _build_logger() -> logging.Logger:
    log = logging.getLogger("ncare")
    # avoid adding handlers twice if this module is imported again
    if log.handlers:
        return log

    log.setLevel(logging.INFO)
    handlers = [
        DailyFileHandler("info.log", only_errors=False),
        DailyFileHandler("error.log", only_errors=True),
        logging.StreamHandler(),  # also print to the console
    ]
    for h in handlers:
        h.setFormatter(logging.Formatter(FORMAT))
        log.addHandler(h)
    return log


logger = _build_logger()
