import base64
import hashlib
import hmac
import json
import logging
from functools import partial
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings
from django.db import transaction
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ams.billing.models import Invoice
from ams.billing.service import BillingService, get_billing_service
from ams.xero.service import XeroBillingService

logger = logging.getLogger(__name__)


@transaction.atomic
def process_events(payload: Dict[str, Any]) -> None:
    if not settings.XERO_TENANT_ID:
        raise Exception("XERO_TENANT_ID setting not configured")

    billing_service: Optional[BillingService] = get_billing_service()
    if not billing_service or not isinstance(billing_service, XeroBillingService):
        return

    billing_service_invoice_ids: List[str] = []

    events = payload["events"]
    for event in events:
        if (
            event["eventCategory"] == "INVOICE"
            and event["eventType"] == "UPDATE"
            and event["tenantId"] == settings.XERO_TENANT_ID
        ):
            billing_service_invoice_id: str = event["resourceId"]

            if Invoice.objects.filter(billing_service_invoice_id=billing_service_invoice_id).exists():
                billing_service_invoice_ids.append(billing_service_invoice_id)

    if billing_service_invoice_ids:
        billing_service.update_invoices(billing_service_invoice_ids)


def verify_request_signature(request: HttpRequest) -> bool:
    if not settings.XERO_WEBHOOK_KEY:
        raise Exception("XERO_WEBHOOK_KEY setting not configured")

    # Verify request is from Xero
    signature = request.headers.get("x-xero-signature")
    generated_signature = base64.b64encode(
        hmac.new(bytes(settings.XERO_WEBHOOK_KEY, "utf8"), request.body, hashlib.sha256).digest()
    ).decode("utf-8")

    if signature != generated_signature:
        return False

    return True


# In order to respond to Xero immediately, defer calling process_events() until after
# the response has been sent. This is a bit of a hack and it would be tidier to use something like celery
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

    return AfterHttpResponse(on_close=partial(process_events, payload), status=200)
