"""Rate limiting utilities for Xero API calls.

This module provides retry logic for handling Xero API rate limit errors.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import TypeVar

from xero_python.exceptions import RateLimitException

logger = logging.getLogger(__name__)

# Maximum total time to spend retrying in seconds
MAX_RETRY_DURATION = 10

# Type variable for function return type
F = TypeVar("F", bound=Callable[..., Any])


def retry_on_rate_limit(max_retries: int = 3) -> Callable[[F], F]:
    """Decorator to retry Xero API calls if rate limited (HTTP 429).

    Implements exponential backoff with a maximum total retry duration cap.
    If Xero's Retry-After header would cause the total retry time to exceed
    MAX_RETRY_DURATION, the call fails immediately with a clear error message.

    Args:
        max_retries: Maximum number of retry attempts (default: 3).

    Returns:
        Decorated function that handles rate limit exceptions.

    Raises:
        RateLimitException: If retries are exhausted or Retry-After exceeds cap.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: RateLimitException | None = None
            total_wait_time = 0.0

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitException as e:
                    last_exception = e

                    # If this is the last attempt, don't retry
                    if attempt >= max_retries:
                        logger.exception(
                            "Xero API rate limit exceeded after %d retries for %s. "
                            "Rate limit problem: %s",
                            max_retries,
                            getattr(func, "__name__", repr(func)),
                            e.rate_limit,
                        )
                        raise

                    # Check if we have a Retry-After header
                    retry_after = _get_retry_after_seconds(e)

                    # Calculate wait time (exponential backoff or Retry-After)
                    wait_time = retry_after if retry_after is not None else 2**attempt

                    # Check if waiting would exceed our maximum total duration
                    if total_wait_time + wait_time > MAX_RETRY_DURATION:
                        seconds_remaining = MAX_RETRY_DURATION - total_wait_time
                        logger.exception(
                            "Xero API rate limit exceeded for %s. "
                            "Retry-After header specifies %d seconds, "
                            "but only %.1f seconds remain within %d second cap. "
                            "Rate limit problem: %s. "
                            "Please try again later.",
                            getattr(func, "__name__", repr(func)),
                            wait_time,
                            max(0, seconds_remaining),
                            MAX_RETRY_DURATION,
                            e.rate_limit,
                        )
                        raise

                    logger.warning(
                        "Xero API rate limit hit for %s (attempt %d/%d). "
                        "Rate limit problem: %s. "
                        "Waiting %.1f seconds before retry...",
                        getattr(func, "__name__", repr(func)),
                        attempt + 1,
                        max_retries,
                        e.rate_limit,
                        wait_time,
                    )

                    time.sleep(wait_time)
                    total_wait_time += wait_time

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            msg = f"Unexpected error in retry logic for {func.__name__}"
            raise RuntimeError(msg)

        return wrapper  # type: ignore[return-value]

    return decorator


def _get_retry_after_seconds(exception: RateLimitException) -> int | None:
    """Extract Retry-After value from rate limit exception headers.

    Args:
        exception: The RateLimitException containing response headers.

    Returns:
        Number of seconds to wait, or None if header not found or invalid.
    """
    try:
        headers = exception.headers
        if not headers:
            return None

        # headers is a list of tuples like [('Retry-After', '30')]
        for header_name, header_value in headers:
            if header_name.lower() == "retry-after":
                return int(header_value)
    except (ValueError, TypeError, AttributeError):
        pass

    return None
