from http import HTTPStatus

import pytest
from django.urls import reverse

from ams.billing.tests.factories import InvoiceFactory

pytestmark = pytest.mark.django_db


class TestInvoiceAdmin:
    def test_mark_update_needed(self, admin_client):
        invoice_1 = InvoiceFactory(update_needed=False)
        invoice_2 = InvoiceFactory(update_needed=False)
        invoice_3 = InvoiceFactory(update_needed=False)

        url = reverse("admin:billing_invoice_changelist")
        response = admin_client.post(
            url,
            {
                "action": "mark_update_needed",
                "_selected_action": [invoice_1.pk, invoice_2.pk],
            },
        )

        assert response.status_code == HTTPStatus.FOUND
        invoice_1.refresh_from_db()
        invoice_2.refresh_from_db()
        invoice_3.refresh_from_db()
        assert invoice_1.update_needed is True
        assert invoice_2.update_needed is True
        assert invoice_3.update_needed is False
        assert invoice_1.update_requested_at is not None
        assert invoice_2.update_requested_at is not None
        assert invoice_3.update_requested_at is None

    def test_change_form_marking_stamps_update_requested_at(self, admin_client):
        invoice = InvoiceFactory(update_needed=False)

        url = reverse("admin:billing_invoice_change", args=[invoice.pk])
        response = admin_client.post(
            url,
            {
                "update_needed": "on",
                "billing_service_invoice_id": invoice.billing_service_invoice_id,
            },
        )

        assert response.status_code == HTTPStatus.FOUND
        invoice.refresh_from_db()
        assert invoice.update_needed is True
        assert invoice.update_requested_at is not None
