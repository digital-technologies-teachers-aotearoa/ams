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
