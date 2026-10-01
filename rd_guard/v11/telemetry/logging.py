"""V11 logging helper for :mod:`rd_guard`.

Provides ``get_logger``, a thin wrapper around the standard library
``logging`` module so real-world integrations (see ``realworld.py``) get a
ready-to-use, consistently formatted logger without adding a new
dependency.
"""

import logging

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured ``logging.Logger`` for ``name``.

    Idempotent: calling this repeatedly for the same ``name`` will not add
    duplicate handlers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger
