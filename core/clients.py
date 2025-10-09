"""Фабрики клиентов для работы с внешними сервисами."""
from __future__ import annotations

from typing import Any, Dict

import httpx

from .config import get_settings


def create_http_client(**overrides: Any) -> httpx.AsyncClient:
    """Создаёт HTTP-клиент с учётом глобальных настроек."""
    settings = get_settings()
    kwargs: Dict[str, Any] = {
        "timeout": overrides.pop("timeout", settings.external_api.timeout),
    }
    if settings.use_proxy and settings.proxy_url:
        kwargs["proxies"] = settings.proxy_url

    kwargs.update(overrides)
    return httpx.AsyncClient(**kwargs)


__all__ = ["create_http_client"]
