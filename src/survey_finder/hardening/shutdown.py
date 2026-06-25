import asyncio
import signal
import sys
from typing import List, Callable, Awaitable, Any
from contextlib import asynccontextmanager

from survey_finder.logging.logger import init_logger

logger = init_logger()


class GracefulShutdown:
    """Graceful shutdown handler."""

    def __init__(self):
        self._shutdown_hooks: List[Callable[[], Awaitable[Any]]] = []
        self._shutdown_event = asyncio.Event()
        self._is_shutting_down = False

    def register(self, hook: Callable[[], Awaitable[Any]]) -> None:
        """Register a shutdown hook."""
        self._shutdown_hooks.append(hook)
        logger.info("shutdown_hook_registered", hook=hook.__name__)

    async def shutdown(self) -> None:
        """Execute all shutdown hooks."""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self._shutdown_event.set()

        logger.info("shutdown_starting", hooks=len(self._shutdown_hooks))

        for hook in self._shutdown_hooks:
            try:
                await hook()
                logger.debug("shutdown_hook_complete", hook=hook.__name__)
            except Exception as e:
                logger.error("shutdown_hook_failed", hook=hook.__name__, error=str(e))

        logger.info("shutdown_complete")

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._is_shutting_down

    def wait_for_shutdown(self) -> asyncio.Event:
        """Get shutdown event."""
        return self._shutdown_event


@asynccontextmanager
async def graceful_shutdown_context(shutdown: GracefulShutdown):
    """Context manager for graceful shutdown."""
    loop = asyncio.get_running_loop()

    # Register signal handlers
    def signal_handler():
        asyncio.create_task(shutdown.shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        yield shutdown
    finally:
        # Clean up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.remove_signal_handler(sig)
