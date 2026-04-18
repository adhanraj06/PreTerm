import logging

from app.core.config import settings


def configure_logging() -> None:
    """Configure a simple logging baseline for local development."""
    level_name = str(settings.log_level).upper()
    level = getattr(logging, level_name, logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # httpx logs every request at INFO — far too noisy for Kalshi polling.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

