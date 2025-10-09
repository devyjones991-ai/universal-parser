"""Асинхронная очередь задач приложения."""
from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from .config import QueueSettings, get_settings

TaskHandler = Callable[..., Awaitable[Any] | Any]


class TaskRoutingError(RuntimeError):
    """Ошибка маршрутизации задачи в очередь."""


@dataclass
class TaskMessage:
    name: str
    args: tuple[Any, ...]
    kwargs: Dict[str, Any]


class TaskQueue:
    """Простая in-memory очередь задач с маршрутизацией."""

    def __init__(self, *, settings: Optional[QueueSettings] = None) -> None:
        config = settings or get_settings().queue
        self._settings = config
        self._concurrency = max(1, config.concurrency)
        self._enabled = config.enabled
        self._routes: Dict[str, TaskHandler] = {}
        self._queue: asyncio.Queue[Optional[TaskMessage]] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._started = False

    def register(self, name: str, handler: TaskHandler) -> None:
        """Регистрирует обработчик задачи."""
        self._routes[name] = handler

    async def enqueue(self, name: str, /, *args: Any, **kwargs: Any) -> None:
        """Добавляет задачу в очередь."""
        if name not in self._routes:
            raise TaskRoutingError(f"Обработчик '{name}' не зарегистрирован")

        if not self._enabled:
            await self._execute_immediately(name, *args, **kwargs)
            return

        await self._queue.put(TaskMessage(name=name, args=args, kwargs=kwargs))

    async def _execute_immediately(self, name: str, *args: Any, **kwargs: Any) -> None:
        handler = self._routes[name]
        result = handler(*args, **kwargs)
        if inspect.isawaitable(result):
            await result

    async def start(self) -> None:
        if self._started or not self._enabled:
            return
        self._started = True
        for _ in range(self._concurrency):
            worker = asyncio.create_task(self._worker())
            self._workers.append(worker)

    async def _worker(self) -> None:
        while True:
            message = await self._queue.get()
            if message is None:
                self._queue.task_done()
                break

            handler = self._routes.get(message.name)
            if handler is None:
                self._queue.task_done()
                raise TaskRoutingError(
                    f"Обработчик '{message.name}' не найден при выполнении"
                )

            try:
                result = handler(*message.args, **message.kwargs)
                if inspect.isawaitable(result):
                    await result
            finally:
                self._queue.task_done()

    async def drain(self) -> None:
        """Дожидается выполнения всех задач в очереди."""
        await self._queue.join()

    async def stop(self) -> None:
        if not self._started:
            return
        for _ in self._workers:
            await self._queue.put(None)
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._started = False


def create_task_queue(settings: Optional[QueueSettings] = None) -> TaskQueue:
    """Фабрика очереди задач."""
    return TaskQueue(settings=settings)


__all__ = [
    "TaskHandler",
    "TaskMessage",
    "TaskQueue",
    "TaskRoutingError",
    "create_task_queue",
]
