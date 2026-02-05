"""Rate limiting utilities for Xero API calls.

This module provides fail-fast error handling for Xero API rate limit errors.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import TypeVar

from xero_python.exceptions import HTTPStatusException
from xero_python.exceptions import RateLimitException

logger = logging.getLogger(__name__)

# Type variable for function return type
F = TypeVar("F", bound=Callable[..., Any])


class XeroRateLimitError(Exception):
    """Exception raised when Xero API rate limit is exceeded.

    Attributes:
        retry_after: Number of seconds to wait before retrying, if available.
        rate_limit_type: Type of rate limit that was exceeded (e.g., 'minute',
        'concurrent').
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        rate_limit_type: str | None = None,
    ):
        super().__init__(message)
        self.retry_after = retry_after
        self.rate_limit_type = rate_limit_type


class XeroTransientError(Exception):
    """Raised when transient Xero API errors persist after all retries.

    Attributes:
        status_code: HTTP status code that failed
        attempts: Number of attempts made
        original_exception: Original HTTPStatusException
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        attempts: int,
        original_exception: Exception,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.attempts = attempts
        self.original_exception = original_exception


def handle_rate_limit() -> Callable[[F], F]:
    """Decorator to handle API rate limit errors (HTTP 429) with fail-fast approach.

    When a rate limit is encountered, this decorator:
    1. Logs the error for monitoring
    2. Extracts retry timing from Retry-After header if available
    3. Raises a clear XeroRateLimitError with actionable message

    No retries are attempted - the request fails immediately with clear guidance.

    Returns:
        Decorated function that converts RateLimitException to XeroRateLimitError.

    Raises:
        XeroRateLimitError: When Xero API rate limit is exceeded.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except RateLimitException as e:
                retry_after = _get_retry_after_seconds(e)
                rate_limit_type = e.rate_limit or "unknown"
                func_name = getattr(func, "__name__", repr(func))

                if retry_after:
                    message = (
                        f"Billing system busy, please try again in {retry_after} "
                        f"seconds. Rate limit: {rate_limit_type}"
                    )
                else:
                    message = (
                        "Billing system busy, please try again in a few moments. "
                        f"Rate limit: {rate_limit_type}"
                    )

                logger.exception(
                    "Xero API rate limit exceeded for %s. "
                    "Rate limit problem: %s. "
                    "Retry after: %s seconds. ",
                    func_name,
                    rate_limit_type,
                    retry_after or "unknown",
                )

                raise XeroRateLimitError(message, retry_after, rate_limit_type) from e

        return wrapper  # type: ignore[return-value]

    return decorator


def _get_retry_after_seconds(exception: RateLimitException) -> int | None:
    """Extract Retry-After value from rate limit exception headers.

    Args:
        exception: The RateLimitException containing response headers.

    Returns:
        Number of seconds indicated in Retry-After header, or None if not found
        or invalid.
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


TRANSIENT_STATUS_CODES = frozenset([404, 500, 502, 503, 504])
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1


def retry_transient_errors(
    max_retries: int = MAX_RETRIES,
    base_backoff: float = BASE_BACKOFF_SECONDS,
) -> Callable[[F], F]:
    """Decorator to retry transient Xero API errors with exponential backoff.

    Retries: 404, 500, 502, 503, 504 (transient errors)
    Doesn't retry: 400, 401, 403 (client errors), 429 (handled separately)
    Backoff: 1s, 2s, 4s (exponential)

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_backoff: Base backoff time in seconds (default: 1)

    Returns:
        Decorated function that retries transient errors.

    Raises:
        XeroTransientError: After all retries exhausted
        HTTPStatusException: For non-retryable errors (immediate)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = getattr(func, "__name__", repr(func))
            attempt = 0
            last_exception = None

            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                except HTTPStatusException as e:
                    last_exception = e
                    status = getattr(e, "status", None)

                    # Non-retryable? Fail immediately
                    if status not in TRANSIENT_STATUS_CODES:
                        logger.debug(
                            "%s failed with non-retryable HTTP %s",
                            func_name,
                            status,
                        )
                        raise

                    # All retries exhausted?
                    if attempt >= max_retries:
                        logger.exception(
                            "%s failed after %d attempts with HTTP %s",
                            func_name,
                            attempt + 1,
                            status,
                        )
                        msg = (
                            f"Billing operation failed after {attempt + 1} attempts "
                            f"due to transient error (HTTP {status})"
                        )
                        raise XeroTransientError(
                            msg,
                            status_code=status,
                            attempts=attempt + 1,
                            original_exception=e,
                        ) from e

                    # Retry with exponential backoff
                    backoff_time = base_backoff * (2**attempt)
                    logger.warning(
                        "%s failed with transient HTTP %s on attempt %d/%d. "
                        "Retrying in %.1fs...",
                        func_name,
                        status,
                        attempt + 1,
                        max_retries + 1,
                        backoff_time,
                    )
                    time.sleep(backoff_time)
                    attempt += 1

            if last_exception:
                raise last_exception
            return None

        return wrapper  # type: ignore[return-value]

    return decorator
