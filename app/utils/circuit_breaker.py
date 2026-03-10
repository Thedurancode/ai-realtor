"""Lightweight circuit breaker for external API calls.

Prevents cascading failures when third-party services (Zillow, ElevenLabs,
VAPI, Lob, etc.) go down. After `fail_threshold` consecutive failures,
the circuit opens and returns a fallback for `recovery_timeout` seconds
instead of hammering the dead service.

Usage:
    from app.utils.circuit_breaker import circuit_breakers

    breaker = circuit_breakers.get("zillow")
    if not breaker.is_available():
        return {"error": "Zillow is temporarily unavailable", "cached": True}

    try:
        result = call_zillow(...)
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        raise
"""
import logging
import time
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    """Simple circuit breaker with three states: closed (OK), open (failing), half-open (testing)."""

    name: str
    fail_threshold: int = 5
    recovery_timeout: int = 60  # seconds before trying again
    _failures: int = field(default=0, init=False, repr=False)
    _last_failure_time: float = field(default=0.0, init=False, repr=False)
    _state: str = field(default="closed", init=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def is_available(self) -> bool:
        """Check if the service is available (circuit closed or half-open)."""
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = "half-open"
                    logger.info("Circuit breaker %s: half-open (testing)", self.name)
                    return True
                return False
            # half-open — allow one request through
            return True

    def record_success(self) -> None:
        """Record a successful call — reset failures."""
        with self._lock:
            if self._state != "closed":
                logger.info("Circuit breaker %s: closed (recovered)", self.name)
            self._failures = 0
            self._state = "closed"

    def record_failure(self) -> None:
        """Record a failed call — open circuit if threshold reached."""
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self.fail_threshold:
                if self._state != "open":
                    logger.warning(
                        "Circuit breaker %s: OPEN after %d failures (blocking for %ds)",
                        self.name, self._failures, self.recovery_timeout,
                    )
                self._state = "open"

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failures


class CircuitBreakerRegistry:
    """Registry of named circuit breakers for external services."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get(self, name: str, fail_threshold: int = 5, recovery_timeout: int = 60) -> CircuitBreaker:
        """Get or create a circuit breaker by name."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    fail_threshold=fail_threshold,
                    recovery_timeout=recovery_timeout,
                )
            return self._breakers[name]

    def status(self) -> dict:
        """Get status of all circuit breakers."""
        with self._lock:
            return {
                name: {
                    "state": cb.state,
                    "failures": cb.failure_count,
                    "fail_threshold": cb.fail_threshold,
                    "recovery_timeout": cb.recovery_timeout,
                }
                for name, cb in self._breakers.items()
            }


# Global registry
circuit_breakers = CircuitBreakerRegistry()
