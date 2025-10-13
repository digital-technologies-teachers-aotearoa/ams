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

from ams.billing.exceptions import SettingNotConfiguredError
from ams.billing.models import Invoice
from ams.billing.services import BillingService
from ams.billing.services import get_billing_service

from .service import XeroBillingService

logger = logging.getLogger(__name__)

INVOICE_FETCH_UPDATE_LIMIT = 20


@transaction.atomic
def fetch_updated_invoice_details(*, raise_exception: bool = False) -> None:
    billing_service: BillingService | None = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        return
    invoices = (
        Invoice.objects.select_for_update(no_key=True)
        .filter(update_needed=True, billing_service_invoice_id__isnull=False)
        .order_by("id")[:INVOICE_FETCH_UPDATE_LIMIT]
    )
    if not invoices:
        return
    billing_service_invoice_ids = [
        invoice.billing_service_invoice_id for invoice in invoices
    ]
    try:
        billing_service.update_invoices(billing_service_invoice_ids)
    except Exception:  # broad to log traceback
        if not raise_exception:
            logger.exception("Error processing invoice updates")
        else:
            raise


def process_invoice_update_events(payload: dict[str, Any]) -> None:
    if not settings.XERO_TENANT_ID:
        setting_name = "XERO_TENANT_ID"
        raise SettingNotConfiguredError(setting_name)
    billing_service: BillingService | None = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        return
    events = payload["events"]
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


def verify_request_signature(request: HttpRequest) -> bool:
    if not settings.XERO_WEBHOOK_KEY:
        setting_name = "XERO_WEBHOOK_KEY"
        raise SettingNotConfiguredError(setting_name)
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
    def __init__(self, on_close: Callable[[], Any], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.on_close = on_close

    def close(self) -> None:
        super().close()
        self.on_close()


@csrf_exempt
def xero_webhooks(request: HttpRequest) -> HttpResponse:
    if not (request.method == "POST" and verify_request_signature(request)):
        return HttpResponse(status=401)
    payload = json.loads(request.body)
    process_invoice_update_events(payload)
    return AfterHttpResponse(on_close=fetch_updated_invoice_details, status=200)
