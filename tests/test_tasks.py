from __future__ import annotations

import asyncio

import pytest

from core.config import QueueSettings
from core.tasks import TaskQueue, TaskRoutingError


@pytest.mark.asyncio
async def test_task_queue_routes_registered_tasks():
    queue = TaskQueue(settings=QueueSettings(enabled=True, concurrency=1))
    result = {}
    event = asyncio.Event()

    def handler(value: int) -> None:
        result["value"] = value
        event.set()

    queue.register("calc", handler)

    await queue.start()
    await queue.enqueue("calc", 42)
    await asyncio.wait_for(event.wait(), timeout=1)
    await queue.drain()
    await queue.stop()

    assert result["value"] == 42


@pytest.mark.asyncio
async def test_task_queue_executes_immediately_when_disabled():
    queue = TaskQueue(settings=QueueSettings(enabled=False))
    calls: list[str] = []

    async def handler(value: str) -> None:
        calls.append(value)

    queue.register("immediate", handler)

    await queue.enqueue("immediate", "ok")

    assert calls == ["ok"]


@pytest.mark.asyncio
async def test_task_queue_raises_for_unknown_route():
    queue = TaskQueue(settings=QueueSettings(enabled=True))

    with pytest.raises(TaskRoutingError):
        await queue.enqueue("missing")
