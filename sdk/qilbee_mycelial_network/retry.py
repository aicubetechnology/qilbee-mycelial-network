"""
Retry strategy with exponential backoff and circuit breaker.

Implements resilient retry logic for API requests with configurable
backoff and circuit breaker pattern.
"""

import asyncio
import time
from typing import Callable, TypeVar, Any
from dataclasses import dataclass
import httpx

T = TypeVar("T")


@dataclass
class CircuitBreakerState:
    """State for circuit breaker pattern."""

    failure_count: int = 0
    last_failure_time: float = 0.0
    is_open: bool = False


class RetryStrategy:
    """
    Retry strategy with exponential backoff and circuit breaker.

    Automatically retries failed requests with increasing delays between attempts.
    Implements circuit breaker to prevent overwhelming failed services.
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
    ):
        """
        Initialize retry strategy.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            max_delay: Maximum delay between retries (seconds)
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Time to wait before half-open state (seconds)
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        self._circuit_state = CircuitBreakerState()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt with exponential backoff."""
        delay = min(
            self.backoff_factor ** attempt,
            self.max_delay,
        )
        return delay

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.max_retries:
            return False

        # Check circuit breaker
        if self._circuit_state.is_open:
            time_since_failure = time.time() - self._circuit_state.last_failure_time
            if time_since_failure < self.circuit_breaker_timeout:
                return False
            else:
                # Half-open state - allow one retry
                self._circuit_state.is_open = False

        # Retry on network errors and server errors
        if isinstance(exception, (httpx.NetworkError, httpx.TimeoutException)):
            return True

        if isinstance(exception, httpx.HTTPStatusError):
            # Retry on 5xx server errors and 429 rate limit
            return exception.response.status_code >= 500 or exception.response.status_code == 429

        return False

    def _record_failure(self):
        """Record failure for circuit breaker."""
        self._circuit_state.failure_count += 1
        self._circuit_state.last_failure_time = time.time()

        if self._circuit_state.failure_count >= self.circuit_breaker_threshold:
            self._circuit_state.is_open = True

    def _record_success(self):
        """Record success, reset circuit breaker."""
        self._circuit_state.failure_count = 0
        self._circuit_state.is_open = False

    async def execute(self, func: Callable[[], Any]) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute

        Returns:
            Result from function

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await func()
                self._record_success()
                return result

            except Exception as e:
                last_exception = e
                self._record_failure()

                if not self._should_retry(e, attempt):
                    raise

                # Calculate delay with jitter
                delay = self._calculate_delay(attempt)
                jitter = delay * 0.1  # 10% jitter
                actual_delay = delay + (asyncio.get_event_loop().time() % jitter)

                await asyncio.sleep(actual_delay)

        # This should not be reached, but handle gracefully
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected retry state")
