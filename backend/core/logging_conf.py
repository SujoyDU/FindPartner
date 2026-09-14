"""Minimal stdlib logging configuration (no external deps).

Call ``configure_logging()`` once at process start (lifespan). Emits JSON-free
key=value lines at INFO by default; set ``LOG_LEVEL=DEBUG`` to go verbose.
"""
import logging
import os
import sys

_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Quiet noisy libs unless we're explicitly debugging.
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "passlib"):
        logging.getLogger(noisy).setLevel(level if level <= logging.DEBUG else logging.WARNING)
    _CONFIGURED = True
