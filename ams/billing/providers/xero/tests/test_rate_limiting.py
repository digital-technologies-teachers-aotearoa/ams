# ruff: noqa: PLR2004

"""Tests for Xero rate limiting utilities."""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from xero_python.exceptions import HTTPStatusException
from xero_python.exceptions import RateLimitException

from ams.billing.providers.xero.rate_limiting import XeroRateLimitError
from ams.billing.providers.xero.rate_limiting import XeroTransientError
from ams.billing.providers.xero.rate_limiting import handle_rate_limit
from ams.billing.providers.xero.rate_limiting import retry_transient_errors


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
        assert error.retry_after == 30
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


class TestRetryTransientErrors:
    """Tests for retry_transient_errors decorator."""

    def test_successful_call_no_retry(self):
        """Successful calls pass through without retry."""
        mock_func = Mock(return_value="success")
        decorated = retry_transient_errors()(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_retries_404_error_then_succeeds(self, mock_sleep):
        """404 error triggers retry and eventually succeeds."""
        mock_func = Mock()
        mock_func.side_effect = [
            HTTPStatusException(status=404, reason="Not Found"),
            "success",
        ]

        decorated = retry_transient_errors()(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_retries_504_error_then_succeeds(self, mock_sleep):
        """504 error triggers retry and eventually succeeds."""
        mock_func = Mock()
        mock_func.side_effect = [
            HTTPStatusException(status=504, reason="Gateway Timeout"),
            "success",
        ]

        decorated = retry_transient_errors()(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_exponential_backoff_timing(self, mock_sleep):
        """Backoff follows exponential pattern: 1s, 2s, 4s."""
        mock_func = Mock()
        mock_func.side_effect = [
            HTTPStatusException(status=503, reason="Service Unavailable"),
            HTTPStatusException(status=503, reason="Service Unavailable"),
            HTTPStatusException(status=503, reason="Service Unavailable"),
            "success",
        ]

        decorated = retry_transient_errors()(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 4
        # Verify exponential backoff: 1s, 2s, 4s
        assert mock_sleep.call_count == 3
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0
        assert mock_sleep.call_args_list[2][0][0] == 4.0

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_raises_transient_error_after_max_retries(self, mock_sleep):
        """XeroTransientError raised after exhausting all retries."""
        mock_func = Mock()
        mock_func.side_effect = HTTPStatusException(
            status=500,
            reason="Internal Server Error",
        )

        decorated = retry_transient_errors()(mock_func)

        with pytest.raises(XeroTransientError) as exc_info:
            decorated()

        error = exc_info.value
        assert error.status_code == 500
        assert error.attempts == 4  # Initial + 3 retries
        assert isinstance(error.original_exception, HTTPStatusException)
        assert "4 attempts" in str(error)
        assert "HTTP 500" in str(error)

        # Verify we tried 4 times total (initial + 3 retries)
        assert mock_func.call_count == 4
        # Verify backoff was applied 3 times
        assert mock_sleep.call_count == 3

    def test_non_retryable_400_propagates_immediately(self):
        """400 errors don't trigger retry."""
        mock_func = Mock()
        mock_func.side_effect = HTTPStatusException(status=400, reason="Bad Request")

        decorated = retry_transient_errors()(mock_func)

        with pytest.raises(HTTPStatusException) as exc_info:
            decorated()

        # Should fail immediately without retry
        assert exc_info.value.status == 400
        assert mock_func.call_count == 1

    def test_non_retryable_401_propagates_immediately(self):
        """401 errors don't trigger retry."""
        mock_func = Mock()
        mock_func.side_effect = HTTPStatusException(status=401, reason="Unauthorized")

        decorated = retry_transient_errors()(mock_func)

        with pytest.raises(HTTPStatusException) as exc_info:
            decorated()

        assert exc_info.value.status == 401
        assert mock_func.call_count == 1

    def test_non_retryable_403_propagates_immediately(self):
        """403 errors don't trigger retry."""
        mock_func = Mock()
        mock_func.side_effect = HTTPStatusException(status=403, reason="Forbidden")

        decorated = retry_transient_errors()(mock_func)

        with pytest.raises(HTTPStatusException) as exc_info:
            decorated()

        assert exc_info.value.status == 403
        assert mock_func.call_count == 1

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_works_with_rate_limit_decorator(self, mock_sleep):
        """Both decorators work together correctly."""

        @handle_rate_limit()
        @retry_transient_errors()
        def test_function():
            """Test function with both decorators."""
            # Simulate a transient error
            raise HTTPStatusException(status=504, reason="Gateway Timeout")

        with pytest.raises(XeroTransientError):
            test_function()

        # Should have tried 4 times (initial + 3 retries)
        assert mock_sleep.call_count == 3

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_each_transient_status_code(self, mock_sleep):
        """Test 404, 500, 502, 503, 504 all trigger retry."""
        transient_codes = [404, 500, 502, 503, 504]

        for status_code in transient_codes:
            mock_sleep.reset_mock()
            mock_func = Mock()
            mock_func.side_effect = [
                HTTPStatusException(status=status_code, reason="Error"),
                "success",
            ]

            decorated = retry_transient_errors()(mock_func)
            result = decorated()

            assert result == "success", f"Failed for status code {status_code}"
            assert mock_func.call_count == 2, f"Wrong call count for {status_code}"
            mock_sleep.assert_called_once_with(1.0)

    def test_preserves_function_metadata(self):
        """Decorator preserves __name__ and __doc__."""

        @retry_transient_errors()
        def test_function():
            """Test docstring."""
            return "result"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring."

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_custom_max_retries(self, mock_sleep):
        """Test custom max_retries parameter."""
        mock_func = Mock()
        mock_func.side_effect = HTTPStatusException(status=500, reason="Error")

        decorated = retry_transient_errors(max_retries=2)(mock_func)

        with pytest.raises(XeroTransientError) as exc_info:
            decorated()

        # Should try 3 times total (initial + 2 retries)
        assert mock_func.call_count == 3
        assert exc_info.value.attempts == 3
        assert mock_sleep.call_count == 2

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_custom_base_backoff(self, mock_sleep):
        """Test custom base_backoff parameter."""
        mock_func = Mock()
        mock_func.side_effect = [
            HTTPStatusException(status=500, reason="Error"),
            HTTPStatusException(status=500, reason="Error"),
            "success",
        ]

        decorated = retry_transient_errors(base_backoff=2)(mock_func)
        result = decorated()

        assert result == "success"
        # Backoff should be 2s, 4s (base=2, exponential)
        assert mock_sleep.call_args_list[0][0][0] == 2.0
        assert mock_sleep.call_args_list[1][0][0] == 4.0

    @patch("ams.billing.providers.xero.rate_limiting.time.sleep")
    def test_handles_exception_with_none_status(self, mock_sleep):
        """Test handling of HTTPStatusException with None status."""
        mock_func = Mock()

        # Create exception and mock getattr to return None for status
        HTTPStatusException(status=200, reason="OK")

        def mock_side_effect(*args, **kwargs):
            # Create an exception where getattr returns None for 'status'
            exc = HTTPStatusException(status=200, reason="OK")
            # Use object.__setattr__ to bypass property setter
            object.__setattr__(exc, "_status", None)
            raise exc

        mock_func.side_effect = mock_side_effect

        decorated = retry_transient_errors()(mock_func)

        # Should not retry if status is None (not in TRANSIENT_STATUS_CODES)
        with pytest.raises(HTTPStatusException):
            decorated()

        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()
