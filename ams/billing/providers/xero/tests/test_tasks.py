"""Tests for Xero async tasks."""

from unittest.mock import patch

import pytest

from ams.billing.providers.xero.rate_limiting import XeroRateLimitError
from ams.billing.providers.xero.tasks.enqueue_tasks import enqueue_invoice_update_task
from ams.billing.providers.xero.tasks.process_tasks import process_invoice_updates_task

pytestmark = pytest.mark.django_db


class TestProcessInvoiceUpdatesTask:
    """Tests for the invoice update task."""

    def test_task_calls_fetch_function(self, xero_settings):
        """Test that task calls fetch_updated_invoice_details."""
        with patch(
            "ams.billing.providers.xero.tasks.process_tasks.fetch_updated_invoice_details",
        ) as mock_fetch:
            mock_fetch.return_value = {
                "updated_count": 2,
                "invoice_numbers": ["INV-001", "INV-002"],
                "invoice_ids": [1, 2],
                "duration_ms": 500.0,
            }

            result = process_invoice_updates_task(webhook_id="test-webhook-123")

            mock_fetch.assert_called_once_with(
                raise_exception=True,
                webhook_id="test-webhook-123",
            )
            expected_count = 2
            assert result["updated_count"] == expected_count

    def test_task_re_raises_rate_limit_error(self, xero_settings):
        """Test that rate limit errors are re-raised for retry."""
        with patch(
            "ams.billing.providers.xero.tasks.process_tasks.fetch_updated_invoice_details",
        ) as mock_fetch:
            mock_fetch.side_effect = XeroRateLimitError(
                "Rate limit exceeded",
                retry_after=60,
                rate_limit_type="minute",
            )

            with pytest.raises(XeroRateLimitError):
                process_invoice_updates_task(webhook_id="test-webhook-123")


class TestEnqueueInvoiceUpdateTask:
    """Tests for task enqueueing."""

    def test_enqueue_returns_task_id(self, xero_settings):
        """Test that enqueueing returns a task ID."""
        with patch(
            "ams.billing.providers.xero.tasks.enqueue_tasks.async_task",
        ) as mock_async:
            mock_async.return_value = "task-id-abc-123"

            task_id = enqueue_invoice_update_task(webhook_id="webhook-xyz")

            assert task_id == "task-id-abc-123"
            mock_async.assert_called_once()
