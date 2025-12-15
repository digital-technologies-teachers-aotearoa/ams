import base64
import hashlib
import hmac
import json
import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.db import transaction
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ams.billing.models import Invoice
from ams.billing.providers.xero.service import XeroBillingService
from ams.billing.services import BillingService
from ams.billing.services import get_billing_service

logger = logging.getLogger(__name__)

INVOICE_FETCH_UPDATE_LIMIT = 30


@transaction.atomic
def fetch_updated_invoice_details(
    *,
    raise_exception: bool = False,
) -> dict[str, Any]:
    """Fetch and update invoice details from Xero for invoices needing updates.

    Queries for up to INVOICE_FETCH_UPDATE_LIMIT invoices that have update_needed=True
    and a billing_service_invoice_id, then fetches their current details from Xero
    and updates the local records.

    This function is typically called after receiving webhook notifications from Xero
    indicating that invoices have been updated.

    Args:
        raise_exception: If True, exceptions are re-raised. If False (default),
            exceptions are logged but not raised.

    Returns:
        Dictionary containing:
        - 'updated_count': Number of invoices updated
        - 'invoice_numbers': List of invoice numbers that were updated
        - 'invoice_ids': List of invoice IDs that were updated
    """
    result = {"updated_count": 0, "invoice_numbers": [], "invoice_ids": []}

    billing_service: BillingService | None = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        return result

    invoices = (
        Invoice.objects.select_for_update(no_key=True)
        .filter(update_needed=True, billing_service_invoice_id__isnull=False)
        .order_by("id")[:INVOICE_FETCH_UPDATE_LIMIT]
    )
    if not invoices:
        logger.info("No invoices need updating")
        return result

    invoice_list = list(invoices)
    billing_service_invoice_ids = [
        invoice.billing_service_invoice_id for invoice in invoice_list
    ]

    logger.info(
        "Fetching updates for %d invoice(s): %s",
        len(invoice_list),
        ", ".join(inv.invoice_number for inv in invoice_list),
    )

    try:
        billing_service.update_invoices(billing_service_invoice_ids)
        result["updated_count"] = len(invoice_list)
        result["invoice_numbers"] = [inv.invoice_number for inv in invoice_list]
        result["invoice_ids"] = [inv.id for inv in invoice_list]
        logger.info(
            "Successfully updated %d invoice(s)",
            len(invoice_list),
        )
    except Exception:  # broad to log traceback
        if not raise_exception:
            logger.exception("Error processing invoice updates")
        else:
            raise

    return result


def process_invoice_update_events(payload: dict[str, Any]) -> bool:
    """Process invoice update events from a Xero webhook payload.

    Parses the webhook payload for INVOICE UPDATE events matching the configured
    tenant, and marks the corresponding local Invoice records as needing updates.

    Args:
        payload: The webhook payload dictionary containing an 'events' key with
            a list of event objects.

    Returns:
        True if any invoice update events were processed, False otherwise.
    """
    billing_service: BillingService | None = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        return False
    events = payload["events"]
    processed_any = False
    for event in events:
        if (
            event["eventCategory"] == "INVOICE"
            and event["eventType"] == "UPDATE"
            and event["tenantId"] == settings.XERO_TENANT_ID
        ):
            billing_service_invoice_id: str = event["resourceId"]
            Invoice.objects.filter(
                billing_service_invoice_id=billing_service_invoice_id,
            ).update(update_needed=True)
            processed_any = True
    return processed_any


def verify_request_signature(request: HttpRequest) -> bool:
    """Verify that a webhook request came from Xero using HMAC signature.

    Computes an HMAC-SHA256 signature of the request body using the configured
    webhook key and compares it to the signature in the x-xero-signature header.

    Args:
        request: The incoming HTTP request to verify.

    Returns:
        True if the signature is valid, False otherwise.
    """
    signature = request.headers.get("x-xero-signature")
    generated_signature = base64.b64encode(
        hmac.new(
            bytes(settings.XERO_WEBHOOK_KEY, "utf8"),
            request.body,
            hashlib.sha256,
        ).digest(),
    ).decode("utf-8")
    return signature == generated_signature


class AfterHttpResponse(HttpResponse):
    """HTTP response that executes a callback after the response is closed.

    This allows for deferred execution of tasks after sending the HTTP response,
    useful for webhook handlers that need to acknowledge receipt quickly before
    performing potentially slow processing.

    Attributes:
        on_close: Callable to execute after the response is closed.
    """

    def __init__(self, on_close: Callable[[], Any], *args: Any, **kwargs: Any) -> None:
        """Initialize the response with a close callback.

        Args:
            on_close: Function to call after the response is closed.
            *args: Arguments to pass to HttpResponse.
            **kwargs: Keyword arguments to pass to HttpResponse.
        """
        super().__init__(*args, **kwargs)
        self.on_close = on_close

    def close(self) -> None:
        """Close the response and execute the on_close callback."""
        super().close()
        self.on_close()


@csrf_exempt
def xero_webhooks(request: HttpRequest) -> HttpResponse:
    """Handle incoming webhook notifications from Xero.

    Verifies the webhook signature, processes invoice update events, and returns
    a 200 response. After the response is sent, triggers a fetch of updated
    invoice details from Xero if any invoice updates were processed.

    Args:
        request: The incoming webhook HTTP request from Xero.

    Returns:
        HttpResponse with status 200 if valid, 401 if invalid.
    """
    if not (request.method == "POST" and verify_request_signature(request)):
        return HttpResponse(status=401)
    payload = json.loads(request.body)
    has_invoice_updates = process_invoice_update_events(payload)
    if has_invoice_updates:
        return AfterHttpResponse(on_close=fetch_updated_invoice_details, status=200)
    return HttpResponse(status=200)
