"""Настройка логирования приложения."""
from __future__ import annotations

import logging
import logging.config
from typing import Optional

from .config import LoggingSettings, get_settings


DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"


def configure_logging(config: Optional[LoggingSettings] = None) -> None:
    """Инициализирует стандартное логирование.

    Если конфигурация не передана, то используется глобальная настройка.
    """

    settings = config or get_settings().logging

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    }

    formatters = {
        "default": {
            "format": DEFAULT_FORMAT,
        }
    }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "root": {
                "handlers": ["console"],
                "level": settings.level.upper(),
            },
        }
    )

    logging.getLogger(__name__).debug("Логирование сконфигурировано")


__all__ = ["configure_logging"]
