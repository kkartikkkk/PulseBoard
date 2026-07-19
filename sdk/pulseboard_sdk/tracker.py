"""
PulseBoard Tracker
Captures request metadata (endpoint, method, status, latency)
and ships it to the PulseBoard ingestion API — either one at a time
or in batches for efficiency.
"""

import time
import asyncio
import threading
import httpx
from datetime import datetime, timezone
from typing import Callable
from collections import deque


PULSEBOARD_URL = "https://your-pulseboard-instance.com"  # override via constructor


class PulseBoardClient:
    """
    Low-level client — use this if you want manual control.
    Supports both sync and async sending.

    Example:
        client = PulseBoardClient(api_key="xxx", base_url="http://localhost:8000")
        client.track(endpoint="/users", method="GET", status_code=200, latency_ms=42.1)
    """

    def __init__(self, api_key: str, base_url: str = PULSEBOARD_URL, batch_size: int = 20, flush_interval: float = 5.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def track(self, endpoint: str, method: str, status_code: int, latency_ms: float,
              user_agent: str = None, error_message: str = None):
        """Queue a single event for batched sending."""
        event = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_agent": user_agent,
            "error_message": error_message,
        }
        with self._lock:
            self._queue.append(event)
            if len(self._queue) >= self.batch_size:
                self._flush_now()

    def _flush_now(self):
        """Drain the queue and POST a batch. Called with lock held."""
        if not self._queue:
            return
        batch = []
        while self._queue:
            batch.append(self._queue.popleft())

        # Fire-and-forget in a new thread so we never block the main request thread
        threading.Thread(target=self._send_batch, args=(batch,), daemon=True).start()

    def _send_batch(self, batch: list):
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(
                    f"{self.base_url}/ingest/batch",
                    json=batch,
                    headers={"x-api-key": self.api_key},
                )
        except Exception:
            pass  # Never crash the caller's process over telemetry

    def _flush_loop(self):
        while True:
            time.sleep(self.flush_interval)
            with self._lock:
                self._flush_now()

    def flush(self):
        """Manually flush — useful in tests or before process shutdown."""
        with self._lock:
            self._flush_now()


class PulseBoardMiddleware:
    """
    ASGI middleware that auto-instruments any FastAPI / Starlette app.

    Usage:
        app.add_middleware(
            PulseBoardMiddleware,
            api_key="your-project-api-key",
            base_url="http://localhost:8000",   # optional, defaults to hosted service
        )
    """

    def __init__(self, app, api_key: str, base_url: str = PULSEBOARD_URL, **kwargs):
        self.app = app
        self.client = PulseBoardClient(api_key=api_key, base_url=base_url, **kwargs)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        user_agent = None

        # Extract user-agent from headers
        for name, value in scope.get("headers", []):
            if name == b"user-agent":
                user_agent = value.decode("utf-8", errors="ignore")
                break

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        error_message = None
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            error_message = str(exc)
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            self.client.track(
                endpoint=path,
                method=method,
                status_code=status_code,
                latency_ms=latency_ms,
                user_agent=user_agent,
                error_message=error_message,
            )
