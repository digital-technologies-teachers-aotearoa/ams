"""Tests for Xero rate limiting utilities."""

from unittest.mock import Mock

import pytest
from xero_python.exceptions import RateLimitException

from ams.billing.providers.xero.rate_limiting import XeroRateLimitError
from ams.billing.providers.xero.rate_limiting import handle_rate_limit


class TestHandleRateLimit:
    """Tests for the handle_rate_limit decorator."""

    def test_successful_call_no_error(self):
        """Test that successful calls pass through without error."""
        mock_func = Mock(return_value="success")
        decorated = handle_rate_limit()(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_raises_xero_rate_limit_error_on_429(self):
        """Test that rate limit exceptions are converted to XeroRateLimitError."""
        mock_func = Mock()
        mock_func.side_effect = RateLimitException(
            http_resp=Mock(status=429, reason="Too Many Requests"),
        )

        decorated = handle_rate_limit()(mock_func)

        with pytest.raises(XeroRateLimitError) as exc_info:
            decorated()

        assert mock_func.call_count == 1
        assert "Billing system busy" in str(exc_info.value)

    def test_includes_retry_after_in_error_message(self):
        """Test that Retry-After header is included in error message."""
        mock_func = Mock()
        mock_resp = Mock(status=429, reason="Too Many Requests")

        exception = RateLimitException(http_resp=mock_resp)
        exception.http_resp.getheaders = Mock(return_value=[("Retry-After", "30")])

        mock_func.side_effect = exception

        decorated = handle_rate_limit()(mock_func)

        with pytest.raises(XeroRateLimitError) as exc_info:
            decorated()

        error = exc_info.value
        assert error.retry_after == 30  # noqa: PLR2004
        assert "30 seconds" in str(error)
        assert mock_func.call_count == 1

    def test_handles_missing_retry_after_header(self):
        """Test graceful handling when Retry-After header is missing."""
        mock_func = Mock()
        mock_resp = Mock(status=429, reason="Too Many Requests")

        exception = RateLimitException(http_resp=mock_resp)
        exception.http_resp.getheaders = Mock(return_value=[])

        mock_func.side_effect = exception

        decorated = handle_rate_limit()(mock_func)

        with pytest.raises(XeroRateLimitError) as exc_info:
            decorated()

        error = exc_info.value
        assert error.retry_after is None
        assert "in a few moments" in str(error)
        assert mock_func.call_count == 1

    def test_includes_rate_limit_type(self):
        """Test that rate limit type is captured in error."""
        mock_func = Mock()
        mock_resp = Mock(status=429, reason="Too Many Requests")
        mock_resp.getheaders = Mock(return_value=[("x-rate-limit-problem", "minute")])

        exception = RateLimitException(http_resp=mock_resp)

        mock_func.side_effect = exception

        decorated = handle_rate_limit()(mock_func)

        with pytest.raises(XeroRateLimitError) as exc_info:
            decorated()

        error = exc_info.value
        # The rate_limit property reads from x-rate-limit-problem header
        assert "Rate limit:" in str(error)

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @handle_rate_limit()
        def test_function():
            """Test docstring."""
            return "result"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."

    def test_no_retries_attempted(self):
        """Test that function is only called once (no retries)."""
        mock_func = Mock()
        call_count = 0

        def side_effect_func(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitException(
                    http_resp=Mock(status=429, reason="Too Many Requests"),
                )
            return "should not reach here"

        mock_func.side_effect = side_effect_func
        decorated = handle_rate_limit()(mock_func)

        with pytest.raises(XeroRateLimitError):
            decorated()

        # Should only be called once, no retries
        assert call_count == 1
        assert mock_func.call_count == 1

    def test_handles_none_headers(self):
        """Test handling when headers attribute returns None."""
        mock_func = Mock()
        mock_resp = Mock(status=429, reason="Too Many Requests")

        exception = RateLimitException(http_resp=mock_resp)
        exception.http_resp.getheaders = Mock(return_value=None)

        mock_func.side_effect = exception

        decorated = handle_rate_limit()(mock_func)

        with pytest.raises(XeroRateLimitError) as exc_info:
            decorated()

        error = exc_info.value
        assert error.retry_after is None
        assert "Billing system busy" in str(error)
