"""Configuración centralizada de logging para Agro Planner."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict


def configure_logging() -> None:
    """Inicializa la configuración de logging para la aplicación."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "INFO",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": "INFO",
                "filename": str(logs_dir / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    }

    logging.config.dictConfig(config)

