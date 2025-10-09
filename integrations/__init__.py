"""Интеграции с внешними сервисами."""
from __future__ import annotations

from typing import Protocol


class IntegrationClient(Protocol):
    """Протокол для внешних клиентов."""

    async def send(self, payload: dict) -> None: ...


__all__ = ["IntegrationClient"]
