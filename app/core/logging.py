from __future__ import annotations

import logging
import sys


def configure_application_logging(log_level: str) -> logging.Logger:
    logger = logging.getLogger("prompt_transformer")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False
    return logger
