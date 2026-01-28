"""Process tasks for Xero billing operations."""

import logging
from typing import Any

from ams.billing.providers.xero.rate_limiting import XeroRateLimitError
from ams.billing.providers.xero.views import fetch_updated_invoice_details

logger = logging.getLogger(__name__)


def process_invoice_updates_task(webhook_id: str | None = None) -> dict[str, Any]:
    """Async task to fetch and update invoice details from Xero.

    This task is enqueued by the webhook handler after marking invoices as
    needing updates. It fetches current invoice details from Xero and updates
    local records.

    Args:
        webhook_id: Optional webhook ID for correlated logging.

    Returns:
        Dictionary containing update results (updated_count, invoice_numbers, etc.)

    Raises:
        XeroRateLimitError: If Xero API rate limit is exceeded. Django-Q2 will
            automatically retry with exponential backoff.
        Exception: Other errors are logged and will trigger retry.
    """
    # Import here to avoid circular import

    log_prefix = f"[Task:{webhook_id}] " if webhook_id else "[Task] "

    logger.info("%sStarting async invoice update task", log_prefix)

    try:
        result = fetch_updated_invoice_details(
            raise_exception=True,  # Raise exceptions to trigger retry
            webhook_id=webhook_id,
        )
    except XeroRateLimitError:
        # Re-raise rate limit errors - Django-Q2 will retry automatically
        logger.warning(
            "%sXero rate limit hit - task will be retried automatically",
            log_prefix,
        )
        raise
    except Exception:
        # Log and re-raise - Django-Q2 will retry
        logger.exception(
            "%sTask failed with exception - will be retried",
            log_prefix,
        )
        raise
    else:
        logger.info(
            "%sTask completed successfully - updated %d invoice(s)",
            log_prefix,
            result["updated_count"],
        )
        return result
