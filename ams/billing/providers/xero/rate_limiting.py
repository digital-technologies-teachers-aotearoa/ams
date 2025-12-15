"""Rate limiting utilities for Xero API calls.

This module provides fail-fast error handling for Xero API rate limit errors.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import TypeVar

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
