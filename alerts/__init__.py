"""Уведомления и алёрты."""

from typing import Iterable, Protocol


class AlertSender(Protocol):
    def __call__(self, message: str) -> None: ...


def notify(senders: Iterable[AlertSender], message: str) -> None:
    """Рассылает сообщение по всем зарегистрированным алёртам."""
    for sender in senders:
        sender(message)


__all__ = ["AlertSender", "notify"]
