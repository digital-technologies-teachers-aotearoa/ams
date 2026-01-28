import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ams.billing.models import Invoice
from ams.billing.providers.xero.service import XeroBillingService
from ams.billing.services import BillingService
from ams.billing.services import get_billing_service
from ams.organisations.mixins import user_is_organisation_admin

logger = logging.getLogger(__name__)

INVOICE_FETCH_UPDATE_LIMIT = 30


@transaction.atomic
def fetch_updated_invoice_details(
    *,
    raise_exception: bool = False,
    webhook_id: str | None = None,
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
        webhook_id: Optional webhook ID for correlated logging.

    Returns:
        Dictionary containing:
        - 'updated_count': Number of invoices updated
        - 'invoice_numbers': List of invoice numbers that were updated
        - 'invoice_ids': List of invoice IDs that were updated
        - 'duration_ms': Time taken in milliseconds
    """
    start_time = time.perf_counter()
    log_prefix = f"[{webhook_id}] " if webhook_id else ""
    result = {
        "updated_count": 0,
        "invoice_numbers": [],
        "invoice_ids": [],
        "duration_ms": 0.0,
    }

    logger.info(
        "%sStarting invoice fetch",
        log_prefix,
    )

    billing_service: BillingService | None = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        logger.warning(
            "%sNo Xero billing service configured, skipping invoice fetch",
            log_prefix,
        )
        result["duration_ms"] = (time.perf_counter() - start_time) * 1000
        return result

    query_start = time.perf_counter()
    invoices = (
        Invoice.objects.select_for_update(no_key=True)
        .filter(update_needed=True, billing_service_invoice_id__isnull=False)
        .order_by("id")[:INVOICE_FETCH_UPDATE_LIMIT]
    )
    invoice_list = list(invoices)
    query_duration_ms = (time.perf_counter() - query_start) * 1000

    if not invoice_list:
        logger.info(
            "%sNo invoices need updating (query took %.2f ms)",
            log_prefix,
            query_duration_ms,
        )
        result["duration_ms"] = (time.perf_counter() - start_time) * 1000
        return result

    billing_service_invoice_ids = [
        invoice.billing_service_invoice_id for invoice in invoice_list
    ]

    logger.info(
        "%sFetching updates for %d invoice(s): %s (query took %.2f ms)",
        log_prefix,
        len(invoice_list),
        ", ".join(inv.invoice_number for inv in invoice_list),
        query_duration_ms,
    )

    api_duration_ms = 0.0
    try:
        api_start = time.perf_counter()
        billing_service.update_invoices(billing_service_invoice_ids)
        api_duration_ms = (time.perf_counter() - api_start) * 1000

        result["updated_count"] = len(invoice_list)
        result["invoice_numbers"] = [inv.invoice_number for inv in invoice_list]
        result["invoice_ids"] = [inv.id for inv in invoice_list]

        logger.info(
            "%sSuccessfully updated %d invoice(s) - api_time=%.2f ms",
            log_prefix,
            len(invoice_list),
            api_duration_ms,
        )
    except Exception:  # broad to log traceback
        api_duration_ms = (time.perf_counter() - api_start) * 1000
        logger.exception(
            "%sError processing invoice updates (failed after %.2f ms)",
            log_prefix,
            api_duration_ms,
        )
        if raise_exception:
            raise

    total_duration_ms = (time.perf_counter() - start_time) * 1000
    result["duration_ms"] = total_duration_ms

    logger.info(
        "%sInvoice fetch complete - total_time=%.2f ms, query_time=%.2f ms, "
        "api_time=%.2f ms, updated=%d",
        log_prefix,
        total_duration_ms,
        query_duration_ms,
        api_duration_ms,
        result["updated_count"],
    )

    return result


def process_invoice_update_events(
    payload: dict[str, Any],
    webhook_id: str | None = None,
) -> bool:
    """Process invoice update events from a Xero webhook payload.

    Parses the webhook payload for INVOICE UPDATE events matching the configured
    tenant, and marks the corresponding local Invoice records as needing updates.

    Args:
        payload: The webhook payload dictionary containing an 'events' key with
            a list of event objects.
        webhook_id: Optional webhook ID for correlated logging.

    Returns:
        True if any invoice update events were processed, False otherwise.
    """
    log_prefix = f"[{webhook_id}] " if webhook_id else ""

    billing_service: BillingService | None = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        logger.warning(
            "%sNo Xero billing service configured, skipping event processing",
            log_prefix,
        )
        return False

    events = payload.get("events", [])
    if not events:
        logger.info("%sNo events in payload", log_prefix)
        return False

    processed_count = 0
    invoice_update_count = 0
    other_event_types = set()

    for event in events:
        event_category = event.get("eventCategory")
        event_type = event.get("eventType")
        tenant_id = event.get("tenantId")
        resource_id = event.get("resourceId")

        logger.debug(
            "%sEvent: category=%s, type=%s, tenant=%s, resource=%s",
            log_prefix,
            event_category,
            event_type,
            tenant_id,
            resource_id,
        )

        if (
            event_category == "INVOICE"
            and event_type == "UPDATE"
            and tenant_id == settings.XERO_TENANT_ID
        ):
            billing_service_invoice_id: str = resource_id
            updated_count = Invoice.objects.filter(
                billing_service_invoice_id=billing_service_invoice_id,
            ).update(update_needed=True)

            if updated_count > 0:
                invoice_update_count += 1
                logger.info(
                    "%sMarked invoice for update: xero_id=%s, updated=%d record(s)",
                    log_prefix,
                    billing_service_invoice_id,
                    updated_count,
                )
            else:
                logger.debug(
                    "%sInvoice not found locally: xero_id=%s",
                    log_prefix,
                    billing_service_invoice_id,
                )

            processed_count += 1
        else:
            other_event_types.add(f"{event_category}:{event_type}")

    if other_event_types:
        logger.debug(
            "%sIgnored event types: %s",
            log_prefix,
            ", ".join(sorted(other_event_types)),
        )

    logger.info(
        "%sProcessed %d invoice update event(s), marked %d invoice(s) for update",
        log_prefix,
        processed_count,
        invoice_update_count,
    )

    return processed_count > 0


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
        try:
            self.on_close()
        except Exception:
            logger.exception("Error in deferred webhook processing")


@login_required
def invoice_redirect(request: HttpRequest, invoice_number: str) -> HttpResponse:
    """Redirect to the online invoice URL.

    Fetches the online invoice URL and redirects the user to view
    the invoice. Only allows access if:
    1. The invoice belongs to the requesting user's account, OR
    2. The invoice belongs to an organisation where the user is an admin

    Args:
        request: The HTTP request.
        invoice_number: The invoice number to redirect to.

    Returns:
        HttpResponseRedirect to the online invoice URL.

    Raises:
        PermissionDenied: If the user doesn't have permission to view the invoice.
    """
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)

    # Check if the user owns this invoice (individual membership)
    user_owns_invoice = (
        hasattr(request.user, "account") and invoice.account == request.user.account
    )

    # Check if the invoice belongs to an organisation where the user is an admin
    user_is_org_admin = False
    if hasattr(invoice.account, "organisation") and invoice.account.organisation:
        user_is_org_admin = user_is_organisation_admin(
            request.user,
            invoice.account.organisation,
        )

    # Deny access if user doesn't own the invoice and isn't an org admin
    if not user_owns_invoice and not user_is_org_admin:
        raise PermissionDenied

    billing_service: BillingService | None = get_billing_service()
    if not billing_service:
        return HttpResponse("Billing service not available", status=503)

    invoice_url = billing_service.get_invoice_url(invoice)
    if not invoice_url:
        return HttpResponse("Invoice URL not available", status=404)

    return HttpResponseRedirect(invoice_url)


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
    webhook_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    payload_size = len(request.body) if request.body else 0
    logger.info(
        "Webhook received [%s] - method=%s, size=%d bytes, ip=%s",
        webhook_id,
        request.method,
        payload_size,
        request.META.get("REMOTE_ADDR", "unknown"),
    )

    logger.debug(
        "Webhook headers [%s] - content_type=%s, user_agent=%s",
        webhook_id,
        request.content_type,
        request.headers.get("user-agent", "unknown"),
    )

    if request.method != "POST":
        logger.warning(
            "Webhook rejected [%s] - invalid method: %s",
            webhook_id,
            request.method,
        )
        return HttpResponse(status=401)

    sig_start = time.perf_counter()
    signature_valid = verify_request_signature(request)
    sig_duration_ms = (time.perf_counter() - sig_start) * 1000

    if not signature_valid:
        logger.warning(
            "Webhook rejected [%s] - invalid signature (verification took %.2f ms)",
            webhook_id,
            sig_duration_ms,
        )
        return HttpResponse(status=401)

    logger.debug(
        "Signature verified [%s] - took %.2f ms",
        webhook_id,
        sig_duration_ms,
    )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        logger.exception(
            "Webhook rejected [%s] - invalid JSON payload",
            webhook_id,
        )
        return HttpResponse(status=400)

    event_count = len(payload.get("events", []))
    logger.info(
        "Webhook payload parsed [%s] - %d event(s)",
        webhook_id,
        event_count,
    )
    logger.debug(
        "Webhook full payload [%s] - %s",
        webhook_id,
        json.dumps(payload, indent=2),
    )

    process_start = time.perf_counter()
    has_invoice_updates = process_invoice_update_events(payload, webhook_id=webhook_id)
    process_duration_ms = (time.perf_counter() - process_start) * 1000

    logger.info(
        "Event processing complete [%s] - has_updates=%s, took %.2f ms",
        webhook_id,
        has_invoice_updates,
        process_duration_ms,
    )

    total_duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "Webhook response sent [%s] - status=200, total_time=%.2f ms, "
        "sig_time=%.2f ms, process_time=%.2f ms",
        webhook_id,
        total_duration_ms,
        sig_duration_ms,
        process_duration_ms,
    )

    if has_invoice_updates:

        def on_close_with_logging() -> None:
            fetch_updated_invoice_details(webhook_id=webhook_id)

        return AfterHttpResponse(on_close=on_close_with_logging, status=200)

    logger.debug("No invoice updates needed [%s]", webhook_id)
    return HttpResponse(status=200)
