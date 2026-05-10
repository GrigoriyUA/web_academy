import time
import sqlite3
from collections import defaultdict, deque

import httpx
import psutil
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from logging_config import setup_logging

setup_logging()
log = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = self._buckets[ip]

        # Видаляємо timestamps за межами вікна
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            retry_after = round(self.window_seconds - (now - bucket[0]), 1)
            log.warning(
                "rate_limit_exceeded",
                ip=ip,
                requests_in_window=len(bucket),
                window_seconds=self.window_seconds,
                retry_after_seconds=retry_after,
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Максимум {self.max_requests} запитів за {self.window_seconds} секунд з одного IP.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        bucket.append(now)
        return await call_next(request)


app = FastAPI()
app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)

DB_PATH = "health.db"
EXTERNAL_API_URL = "https://api.groq.com"


def _check_db() -> dict:
    try:
        start = time.monotonic()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        latency = round((time.monotonic() - start) * 1000, 2)
        return {"status": "ok", "latency_ms": latency}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _check_external_api() -> dict:
    try:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=5) as client:
            await client.get(EXTERNAL_API_URL)
        latency = round((time.monotonic() - start) * 1000, 2)
        return {"status": "ok", "latency_ms": latency, "url": EXTERNAL_API_URL}
    except Exception as e:
        return {"status": "error", "error": str(e), "url": EXTERNAL_API_URL}


def _check_system() -> dict:
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    status = "warning" if cpu > 90 or ram.percent > 90 else "ok"
    return {
        "status": status,
        "cpu_percent": cpu,
        "ram_percent": round(ram.percent, 1),
        "ram_available_mb": round(ram.available / 1024 / 1024, 1),
    }


@app.get("/api/v1/health")
async def health():
    db = _check_db()
    api = await _check_external_api()
    system = _check_system()

    checks = {"database": db, "external_api": api, "system": system}
    overall_ok = all(c["status"] == "ok" for c in checks.values())
    status = "ok" if overall_ok else "degraded"

    log.info(
        "health_check",
        status=status,
        db=db["status"],
        api=api["status"],
        system=system["status"],
    )

    return JSONResponse(
        content={"status": status, "checks": checks},
        status_code=200 if overall_ok else 503,
    )
