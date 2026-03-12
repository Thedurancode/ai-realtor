"""Prometheus metrics middleware for request monitoring."""
import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed — metrics disabled")

if PROMETHEUS_AVAILABLE:
    REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )
    REQUEST_LATENCY = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )
    ACTIVE_REQUESTS = Gauge(
        "http_requests_active",
        "Number of active HTTP requests",
    )
    CIRCUIT_BREAKER_STATE = Gauge(
        "circuit_breaker_open",
        "Circuit breaker state (1=open, 0=closed)",
        ["service"],
    )
    JOB_QUEUE_DEPTH = Gauge(
        "job_queue_depth",
        "Number of pending background jobs",
    )
    ERROR_COUNT = Counter(
        "http_errors_total",
        "Total HTTP errors by type",
        ["error_type"],
    )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect request metrics for Prometheus."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)

        # Skip metrics for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        # Normalize path to avoid cardinality explosion
        path = self._normalize_path(request.url.path)

        ACTIVE_REQUESTS.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(method=method, endpoint=path, status_code=response.status_code).inc()
            return response
        except Exception as e:
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            elapsed = time.perf_counter() - start
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(elapsed)
            ACTIVE_REQUESTS.dec()

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Replace dynamic path segments with placeholders to limit cardinality."""
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            # Replace UUIDs and numeric IDs with placeholder
            if part.isdigit() or (len(part) == 36 and "-" in part):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized) if normalized else "/"


def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics scrape endpoint."""
    if not PROMETHEUS_AVAILABLE:
        return Response(content="prometheus_client not installed", status_code=501)

    # Update circuit breaker metrics
    try:
        from app.utils.circuit_breaker import circuit_breakers
        for name, status in circuit_breakers.status().items():
            CIRCUIT_BREAKER_STATE.labels(service=name).set(1 if status["state"] == "open" else 0)
    except Exception:
        pass

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
