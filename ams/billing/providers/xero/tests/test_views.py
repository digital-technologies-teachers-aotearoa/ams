# ruff: noqa: SLF001

"""Tests for Xero webhook views."""

import base64
import hashlib
import hmac
import json
from http import HTTPStatus
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory

from ams.billing.models import Invoice
from ams.billing.providers.mock.service import MockBillingService
from ams.billing.providers.xero.service import XeroBillingService
from ams.billing.providers.xero.views import fetch_updated_invoice_details
from ams.billing.providers.xero.views import invoice_redirect
from ams.billing.providers.xero.views import process_invoice_update_events
from ams.billing.providers.xero.views import verify_request_signature
from ams.billing.providers.xero.views import xero_webhooks
from ams.billing.tests.factories import InvoiceFactory
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestVerifyRequestSignature:
    """Tests for webhook signature verification."""

    def test_verify_valid_signature(self, xero_settings, rf: RequestFactory):
        """Test that valid signature passes verification."""
        payload = {"test": "data"}
        payload_bytes = json.dumps(payload).encode("utf-8")

        signature = base64.b64encode(
            hmac.new(
                xero_settings.XERO_WEBHOOK_KEY.encode("utf-8"),
                payload_bytes,
                hashlib.sha256,
            ).digest(),
        ).decode("utf-8")

        request = rf.post(
            "/billing/xero/webhooks/",
            data=payload_bytes,
            content_type="application/json",
        )
        request.META["HTTP_X_XERO_SIGNATURE"] = signature
        request._body = payload_bytes

        assert verify_request_signature(request) is True

    def test_verify_invalid_signature(self, xero_settings, rf: RequestFactory):
        """Test that invalid signature fails verification."""
        payload = {"test": "data"}
        payload_bytes = json.dumps(payload).encode("utf-8")

        request = rf.post(
            "/billing/xero/webhooks/",
            data=payload_bytes,
            content_type="application/json",
        )
        request.META["HTTP_X_XERO_SIGNATURE"] = "invalid-signature"
        request._body = payload_bytes

        assert verify_request_signature(request) is False

    def test_verify_missing_signature(self, xero_settings, rf: RequestFactory):
        """Test that missing signature fails verification."""
        payload = {"test": "data"}
        payload_bytes = json.dumps(payload).encode("utf-8")

        request = rf.post(
            "/billing/xero/webhooks/",
            data=payload_bytes,
            content_type="application/json",
        )
        request._body = payload_bytes

        # No signature in headers - should use None in comparison
        assert verify_request_signature(request) is False


class TestProcessInvoiceUpdateEvents:
    """Tests for processing webhook events."""

    def test_process_invoice_update_event(
        self,
        xero_settings,
        invoice_user,
        webhook_payload,
    ):
        """Test processing invoice update event."""
        invoice_user.billing_service_invoice_id = "test-invoice-id-123"
        invoice_user.update_needed = False
        invoice_user.save()

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            result = process_invoice_update_events(webhook_payload)

        # Verify invoice was marked for update
        invoice_user.refresh_from_db()
        assert invoice_user.update_needed is True
        assert result is True

    def test_process_multiple_invoice_events(self, xero_settings, invoice_user):
        """Test processing multiple invoice update events."""
        invoice_user.billing_service_invoice_id = "invoice-1"
        invoice_user.save()

        invoice_2 = Invoice.objects.create(
            account=invoice_user.account,
            invoice_number="INV-002",
            billing_service_invoice_id="invoice-2",
            issue_date="2024-01-15",
            due_date="2024-02-15",
            amount=200,
            due=200,
            paid=0,
        )

        payload = {
            "events": [
                {
                    "resourceId": "invoice-1",
                    "eventType": "UPDATE",
                    "eventCategory": "INVOICE",
                    "tenantId": xero_settings.XERO_TENANT_ID,
                },
                {
                    "resourceId": "invoice-2",
                    "eventType": "UPDATE",
                    "eventCategory": "INVOICE",
                    "tenantId": xero_settings.XERO_TENANT_ID,
                },
            ],
        }

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            result = process_invoice_update_events(payload)

        invoice_user.refresh_from_db()
        invoice_2.refresh_from_db()
        assert invoice_user.update_needed is True
        assert invoice_2.update_needed is True
        assert result is True

    def test_process_ignores_non_invoice_events(self, xero_settings, invoice_user):
        """Test that non-invoice events are ignored."""
        invoice_user.billing_service_invoice_id = "test-invoice"
        invoice_user.update_needed = False
        invoice_user.save()

        payload = {
            "events": [
                {
                    "resourceId": "test-invoice",
                    "eventType": "UPDATE",
                    "eventCategory": "CONTACT",  # Not INVOICE
                    "tenantId": xero_settings.XERO_TENANT_ID,
                },
            ],
        }

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            result = process_invoice_update_events(payload)

        invoice_user.refresh_from_db()
        assert invoice_user.update_needed is False
        assert result is False

    def test_process_ignores_wrong_tenant_events(self, xero_settings, invoice_user):
        """Test that events from wrong tenant are ignored."""
        invoice_user.billing_service_invoice_id = "test-invoice"
        invoice_user.update_needed = False
        invoice_user.save()

        payload = {
            "events": [
                {
                    "resourceId": "test-invoice",
                    "eventType": "UPDATE",
                    "eventCategory": "INVOICE",
                    "tenantId": "wrong-tenant-id",
                },
            ],
        }

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            result = process_invoice_update_events(payload)

        invoice_user.refresh_from_db()
        assert invoice_user.update_needed is False
        assert result is False

    def test_process_with_no_billing_service(self, xero_settings):
        """Test that processing handles no billing service gracefully."""
        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_get_service.return_value = None

            result = process_invoice_update_events({"events": []})
            assert result is False

    def test_process_with_non_xero_billing_service(self, xero_settings):
        """Test that processing handles non-Xero billing service gracefully."""
        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_get_service.return_value = MockBillingService()

            result = process_invoice_update_events({"events": []})
            assert result is False


class TestFetchUpdatedInvoiceDetails:
    """Tests for fetching invoice updates."""

    def test_fetch_updated_invoice_details(self, xero_settings, invoice_user):
        """Test fetching updated invoice details."""
        invoice_user.billing_service_invoice_id = "test-invoice"
        invoice_user.update_needed = True
        invoice_user.save()

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            fetch_updated_invoice_details()

        mock_service.update_invoices.assert_called_once()
        call_args = mock_service.update_invoices.call_args[0][0]
        assert "test-invoice" in call_args

    def test_fetch_with_no_billing_service(self):
        """Test fetch handles no billing service gracefully."""
        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_get_service.return_value = None

            # Should not raise any errors
            fetch_updated_invoice_details()

    def test_fetch_with_non_xero_service(self):
        """Test fetch handles non-Xero service gracefully."""
        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_get_service.return_value = MockBillingService()

            # Should not raise any errors
            fetch_updated_invoice_details()

    def test_fetch_with_no_invoices_needing_update(self):
        """Test fetch handles no invoices to update."""
        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            fetch_updated_invoice_details()

        # Should not call update_invoices if no invoices need updating
        mock_service.update_invoices.assert_not_called()

    def test_fetch_limits_invoices(self, xero_settings, account_user):
        """Test that fetch is limited to 10 invoices at a time."""
        # Create 35 invoices needing updates
        for i in range(35):
            Invoice.objects.create(
                account=account_user,
                invoice_number=f"INV-{i:03d}",
                billing_service_invoice_id=f"invoice-{i}",
                issue_date="2024-01-15",
                due_date="2024-02-15",
                amount=100,
                due=100,
                paid=0,
                update_needed=True,
            )

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            fetch_updated_invoice_details()

        # Should only fetch 10
        mock_service.update_invoices.assert_called_once()
        call_args = mock_service.update_invoices.call_args[0][0]
        assert len(call_args) == 10  # noqa: PLR2004

    def test_fetch_logs_exceptions(self, xero_settings, invoice_user):
        """Test that exceptions are logged."""
        invoice_user.billing_service_invoice_id = "test-invoice"
        invoice_user.update_needed = True
        invoice_user.save()

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_service.update_invoices.side_effect = Exception("API Error")
            mock_get_service.return_value = mock_service

            with patch("ams.billing.providers.xero.views.logger") as mock_logger:
                # Should not raise exception by default
                fetch_updated_invoice_details()

                mock_logger.exception.assert_called_once()

    def test_fetch_raises_when_flag_set(self, xero_settings, invoice_user):
        """Test that exceptions are raised when raise_exception=True."""
        invoice_user.billing_service_invoice_id = "test-invoice"
        invoice_user.update_needed = True
        invoice_user.save()

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
        ) as mock_get_service:
            mock_service = Mock(spec=XeroBillingService)
            mock_service.update_invoices.side_effect = ValueError("Test error")
            mock_get_service.return_value = mock_service

            with pytest.raises(ValueError):  # noqa: PT011
                fetch_updated_invoice_details(raise_exception=True)


class TestXeroWebhooks:
    """Tests for webhook endpoint."""

    def test_webhook_returns_401_for_invalid_signature(
        self,
        xero_settings,
        rf: RequestFactory,
        webhook_payload,
    ):
        """Test that invalid signature returns 401."""
        payload_bytes = json.dumps(webhook_payload).encode("utf-8")

        request = rf.post(
            "/billing/xero/webhooks/",
            data=payload_bytes,
            content_type="application/json",
        )
        request.META["HTTP_X_XERO_SIGNATURE"] = "invalid-signature"
        request._body = payload_bytes

        response = xero_webhooks(request)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_webhook_returns_401_for_get_request(
        self,
        xero_settings,
        rf: RequestFactory,
    ):
        """Test that GET request returns 401."""
        request = rf.get("/billing/xero/webhooks/")
        response = xero_webhooks(request)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_webhook_with_invoice_updates_enqueues_task(
        self,
        xero_settings,
        rf: RequestFactory,
        webhook_payload,
    ):
        """Test that webhook with invoice updates enqueues async task."""
        payload_bytes = json.dumps(webhook_payload).encode("utf-8")

        signature = base64.b64encode(
            hmac.new(
                xero_settings.XERO_WEBHOOK_KEY.encode("utf-8"),
                payload_bytes,
                hashlib.sha256,
            ).digest(),
        ).decode("utf-8")

        request = rf.post(
            "/billing/xero/webhooks/",
            data=payload_bytes,
            content_type="application/json",
        )
        request.META["HTTP_X_XERO_SIGNATURE"] = signature
        request._body = payload_bytes

        with (
            patch(
                "ams.billing.providers.xero.views.get_billing_service",
            ) as mock_get_service,
            patch(
                "ams.billing.providers.xero.views.enqueue_invoice_update_task",
            ) as mock_enqueue,
        ):
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service
            mock_enqueue.return_value = "test-task-id-123"

            response = xero_webhooks(request)

        assert response.status_code == HTTPStatus.OK
        # Verify task was enqueued
        mock_enqueue.assert_called_once()

    def test_webhook_without_invoice_updates_does_not_enqueue_task(
        self,
        xero_settings,
        rf: RequestFactory,
    ):
        """Test that webhook without invoice updates does not enqueue task."""
        payload = {
            "events": [
                {
                    "resourceId": "test-contact",
                    "eventType": "UPDATE",
                    "eventCategory": "CONTACT",  # Not INVOICE
                    "tenantId": xero_settings.XERO_TENANT_ID,
                },
            ],
        }
        payload_bytes = json.dumps(payload).encode("utf-8")

        signature = base64.b64encode(
            hmac.new(
                xero_settings.XERO_WEBHOOK_KEY.encode("utf-8"),
                payload_bytes,
                hashlib.sha256,
            ).digest(),
        ).decode("utf-8")

        request = rf.post(
            "/billing/xero/webhooks/",
            data=payload_bytes,
            content_type="application/json",
        )
        request.META["HTTP_X_XERO_SIGNATURE"] = signature
        request._body = payload_bytes

        with (
            patch(
                "ams.billing.providers.xero.views.get_billing_service",
            ) as mock_get_service,
            patch(
                "ams.billing.providers.xero.views.enqueue_invoice_update_task",
            ) as mock_enqueue,
        ):
            mock_service = Mock(spec=XeroBillingService)
            mock_get_service.return_value = mock_service

            response = xero_webhooks(request)

        assert response.status_code == HTTPStatus.OK
        # Verify task was NOT enqueued
        mock_enqueue.assert_not_called()


class TestInvoiceRedirect:
    """Tests for invoice redirect view."""

    def test_redirect_to_invoice_url(
        self,
        rf: RequestFactory,
        user,
        invoice_user,
        xero_settings,
    ):
        """Test successful redirect to Xero invoice URL."""
        invoice_user.billing_service_invoice_id = "test-invoice-id-123"
        invoice_user.save()

        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = user

        mock_service = Mock(spec=XeroBillingService)
        mock_service.get_invoice_url.return_value = "https://xero.com/invoice/view/123"

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
            return_value=mock_service,
        ):
            response = invoice_redirect(request, invoice_user.invoice_number)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == "https://xero.com/invoice/view/123"
        mock_service.get_invoice_url.assert_called_once_with(invoice_user)

    def test_redirect_requires_authentication(
        self,
        client,
        invoice_user,
    ):
        """Test that unauthenticated users are redirected to login."""
        response = client.get(f"/billing/invoice/{invoice_user.invoice_number}/")

        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_redirect_rejects_wrong_user(
        self,
        rf: RequestFactory,
        user,
        invoice_user,
    ):
        """Test that users cannot access other users' invoices."""
        # Create a different user
        other_user = UserFactory()

        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = other_user

        with pytest.raises(PermissionDenied):
            invoice_redirect(request, invoice_user.invoice_number)

    def test_redirect_rejects_user_without_account(
        self,
        rf: RequestFactory,
        invoice_user,
    ):
        """Test that users without an account cannot access invoices."""
        # Create a user without an account
        user_no_account = UserFactory()

        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = user_no_account

        with pytest.raises(PermissionDenied):
            invoice_redirect(request, invoice_user.invoice_number)

    def test_redirect_returns_404_for_nonexistent_invoice(
        self,
        rf: RequestFactory,
        user,
    ):
        """Test that nonexistent invoice returns 404."""
        request = rf.get("/billing/invoice/99999/")
        request.user = user

        with pytest.raises(Http404):
            invoice_redirect(request, 99999)

    def test_redirect_returns_503_when_billing_service_unavailable(
        self,
        rf: RequestFactory,
        user,
        invoice_user,
    ):
        """Test that unavailable billing service returns 503."""
        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = user

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
            return_value=None,
        ):
            response = invoice_redirect(request, invoice_user.invoice_number)

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert b"Billing service not available" in response.content

    def test_redirect_returns_503_when_no_billing_service(
        self,
        rf: RequestFactory,
        user,
        invoice_user,
    ):
        """Test that non-Xero billing service returns 503."""
        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = user

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
            return_value=None,
        ):
            response = invoice_redirect(request, invoice_user.invoice_number)

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    def test_redirect_returns_404_when_invoice_url_not_available(
        self,
        rf: RequestFactory,
        user,
        invoice_user,
    ):
        """Test that missing invoice URL returns 404."""
        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = user

        mock_service = Mock(spec=XeroBillingService)
        mock_service.get_invoice_url.return_value = None

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
            return_value=mock_service,
        ):
            response = invoice_redirect(request, invoice_user.invoice_number)

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert b"Invoice URL not available" in response.content

    def test_organisation_admin_can_access_organisation_invoice(
        self,
        rf: RequestFactory,
        organisation,
        account_organisation,
        xero_settings,
    ):
        """Test that organisation admins can access organisation invoices."""
        # Create an organisation admin
        admin_user = UserFactory()
        OrganisationMemberFactory(
            user=admin_user,
            organisation=organisation,
            role=OrganisationMember.Role.ADMIN,
        )

        # Create invoice for the organisation
        invoice = InvoiceFactory(account=account_organisation)
        invoice.billing_service_invoice_id = "test-invoice-id-org"
        invoice.save()

        request = rf.get(f"/billing/invoice/{invoice.invoice_number}/")
        request.user = admin_user

        mock_service = Mock(spec=XeroBillingService)
        mock_service.get_invoice_url.return_value = "https://xero.com/invoice/view/123"

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
            return_value=mock_service,
        ):
            response = invoice_redirect(request, invoice.invoice_number)

        # Admin should be able to access
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == "https://xero.com/invoice/view/123"

    def test_organisation_regular_member_cannot_access_organisation_invoice(
        self,
        rf: RequestFactory,
        organisation,
        account_organisation,
    ):
        """Test that non-admin organisation members cannot access organisation
        invoices."""
        # Create a regular (non-admin) organisation member
        regular_user = UserFactory()
        OrganisationMemberFactory(
            user=regular_user,
            organisation=organisation,
            role=OrganisationMember.Role.MEMBER,  # Regular member, not admin
        )

        # Create invoice for the organisation
        invoice = InvoiceFactory(account=account_organisation)
        invoice.billing_service_invoice_id = "test-invoice-id-org"
        invoice.save()

        request = rf.get(f"/billing/invoice/{invoice.invoice_number}/")
        request.user = regular_user

        # Regular member should NOT be able to access
        with pytest.raises(PermissionDenied):
            invoice_redirect(request, invoice.invoice_number)

    def test_non_member_cannot_access_organisation_invoice(
        self,
        rf: RequestFactory,
        organisation,
        account_organisation,
    ):
        """Test that non-members cannot access organisation invoices."""
        # Create a user who is not a member of the organisation
        non_member_user = UserFactory()

        # Create invoice for the organisation
        invoice = InvoiceFactory(account=account_organisation)
        invoice.billing_service_invoice_id = "test-invoice-id-org"
        invoice.save()

        request = rf.get(f"/billing/invoice/{invoice.invoice_number}/")
        request.user = non_member_user

        # Non-member should NOT be able to access
        with pytest.raises(PermissionDenied):
            invoice_redirect(request, invoice.invoice_number)

    def test_user_can_access_own_individual_invoice(
        self,
        rf: RequestFactory,
        user,
        invoice_user,
        xero_settings,
    ):
        """Test that users can access their own individual membership invoices."""
        invoice_user.billing_service_invoice_id = "test-invoice-id-individual"
        invoice_user.save()

        request = rf.get(f"/billing/invoice/{invoice_user.invoice_number}/")
        request.user = user

        mock_service = Mock(spec=XeroBillingService)
        mock_service.get_invoice_url.return_value = "https://xero.com/invoice/view/456"

        with patch(
            "ams.billing.providers.xero.views.get_billing_service",
            return_value=mock_service,
        ):
            response = invoice_redirect(request, invoice_user.invoice_number)

        # User should be able to access their own invoice
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == "https://xero.com/invoice/view/456"
