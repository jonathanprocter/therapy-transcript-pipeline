import asyncio
import contextlib
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskQueue:
    """Simple asynchronous background task queue."""

    def __init__(self):
        self._queue = asyncio.Queue()
        self._worker = None

    async def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._worker_loop())

    async def add_task(self, coro) -> None:
        await self._queue.put(coro)

    async def _worker_loop(self) -> None:
        while True:
            coro = await self._queue.get()
            try:
                await coro
            except Exception as exc:
                logger.error(f"Background task error: {exc}")
            self._queue.task_done()

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker

