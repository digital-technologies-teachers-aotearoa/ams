import base64
import hashlib
import hmac
import json
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from xero_python.accounting import Invoice as AccountingInvoice

from ams.billing.models import Account, Invoice
from ams.test.utils import any_user

if "ams.xero" not in settings.INSTALLED_APPS:
    pytest.skip(reason="ams.xero not in INSTALLED_APPS", allow_module_level=True)


@override_settings(
    BILLING_SERVICE_CLASS="ams.xero.service.MockXeroBillingService",
    XERO_WEBHOOK_KEY="xero-webhook-key",
    XERO_TENANT_ID="xero-tenant-id",
)
class XeroWebhooksTests(TestCase):
    def setUp(self) -> None:
        self.url = "/xero/webhooks/"

    def _generate_signature(self, request_body: bytes) -> str:
        return base64.b64encode(
            hmac.new(bytes(settings.XERO_WEBHOOK_KEY, "utf8"), request_body, hashlib.sha256).digest()
        ).decode("utf-8")

    def test_should_allow_request_with_valid_signature(self) -> None:
        # Given
        payload: Dict[str, Any] = {"events": []}

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)

        # Then
        self.assertEqual(response.status_code, 200)

    def test_should_not_include_cookies_in_response(self) -> None:
        # Given
        payload: Dict[str, Any] = {"events": []}

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Set-Cookie"), None)

    def test_should_disallow_request_with_invalid_signature(self) -> None:
        # Given
        payload: Dict[str, Any] = {"events": []}

        request_body = json.dumps(payload)
        headers = {"x-xero-signature": "invalid signature"}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)

        # Then
        self.assertEqual(response.status_code, 401)

    @patch("ams.xero.service.MockXeroBillingService._get_xero_invoices")
    def test_should_update_invoice(self, mock__get_xero_invoices: Mock) -> None:
        # Given
        invoice_number = "INV-1234"
        billing_service_invoice_id = "c576f965-e2fb-359f-7ea8-135424ae31d6"

        user = any_user()
        Account.objects.create(user=user)

        invoice = Invoice.objects.create(
            account=user.account,
            billing_service_invoice_id=billing_service_invoice_id,
            invoice_number=invoice_number,
            issue_date=timezone.localdate(),
            due_date=timezone.localdate() + relativedelta(months=1),
            amount=100,
            due=100,
            paid=0,
        )

        updated_invoice = AccountingInvoice(
            invoice_id=billing_service_invoice_id,
            invoice_number=invoice_number,
            date=timezone.localdate() + relativedelta(days=1),
            due_date=timezone.localdate() + relativedelta(months=2),
            total=101,
            amount_due=99,
            amount_paid=2,
        )

        mock__get_xero_invoices.return_value = [updated_invoice]

        payload = {
            "events": [
                {
                    "eventCategory": "INVOICE",
                    "eventType": "UPDATE",
                    "tenantId": settings.XERO_TENANT_ID,
                    "resourceId": updated_invoice.invoice_id,
                }
            ]
        }

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Then
        mock__get_xero_invoices.assert_called_with([updated_invoice.invoice_id])

        invoice.refresh_from_db()

        self.assertEqual(invoice.billing_service_invoice_id, billing_service_invoice_id)
        self.assertEqual(invoice.invoice_number, invoice_number)
        self.assertEqual(invoice.issue_date, updated_invoice.date)
        self.assertEqual(invoice.due_date, updated_invoice.due_date)
        self.assertEqual(invoice.amount, updated_invoice.total)
        self.assertEqual(invoice.paid, updated_invoice.amount_paid)
        self.assertEqual(invoice.due, updated_invoice.amount_due)

    @patch("ams.xero.service.MockXeroBillingService.update_invoices")
    def test_should_not_update_unknown_invoice(self, mock_update_invoices: Mock) -> None:
        # Given
        unknown_invoice = AccountingInvoice(
            invoice_id="f376f962-d2fe-259c-6fa1-235424ae31d5",
            invoice_number="INV-9999",
            date=timezone.localdate() + relativedelta(days=1),
            due_date=timezone.localdate() + relativedelta(months=2),
            total=123,
            amount_due=23,
            amount_paid=100,
        )

        payload = {
            "events": [
                {
                    "eventCategory": "INVOICE",
                    "eventType": "UPDATE",
                    "tenantId": settings.XERO_TENANT_ID,
                    "resourceId": unknown_invoice.invoice_id,
                }
            ]
        }

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Then
        mock_update_invoices.assert_not_called()

    @patch("ams.xero.service.MockXeroBillingService._get_xero_invoices")
    def test_should_ignore_event_for_different_tenant(self, mock__get_xero_invoices: Mock) -> None:
        # Given
        payload = {
            "events": [
                {
                    "eventCategory": "INVOICE",
                    "eventType": "UPDATE",
                    "tenantId": "different-tenant-id",
                    "resourceId": "invoice-id",
                }
            ]
        }

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Then
        mock__get_xero_invoices.assert_not_called()

    @patch("ams.xero.service.MockXeroBillingService._get_xero_invoices")
    def test_should_ignore_non_update_event(self, mock__get_xero_invoices: Mock) -> None:
        # Given
        payload = {
            "events": [
                {
                    "eventCategory": "INVOICE",
                    "eventType": "CREATE",
                    "tenantId": settings.XERO_TENANT_ID,
                    "resourceId": "invoice-id",
                }
            ]
        }

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Then
        mock__get_xero_invoices.assert_not_called()

    @patch("ams.xero.service.MockXeroBillingService._get_xero_invoices")
    def test_should_ignore_non_invoice_event(self, mock__get_xero_invoices: Mock) -> None:
        # Given
        payload = {
            "events": [
                {
                    "eventCategory": "CONTACT",
                    "eventType": "UPDATE",
                    "tenantId": settings.XERO_TENANT_ID,
                    "resourceId": "invoice-id",
                }
            ]
        }

        request_body = json.dumps(payload).encode("utf-8")
        headers = {"x-xero-signature": self._generate_signature(request_body)}

        # When
        response = self.client.post(self.url, content_type="application/json", data=request_body, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Then
        mock__get_xero_invoices.assert_not_called()
