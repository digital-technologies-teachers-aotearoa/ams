from datetime import date
from typing import Any

from django.contrib.auth.models import User

from ams.billing.models import Account
from ams.billing.models import Invoice
from ams.billing.services import BillingService
from ams.memberships.models import Organisation


class MockBillingService(BillingService):
    """Mock billing service for testing and development."""

    def update_user_billing_details(self, user: User) -> None:
        return

    def update_organisation_billing_details(self, organisation: Organisation) -> None:
        return

    def create_invoice(
        self,
        account: Account,
        date: date,
        due_date: date,
        line_items: list[dict[str, Any]],
    ) -> Invoice:
        total = 0
        for line_item in line_items:
            total += line_item["unit_amount"] * line_item["quantity"]

        invoice: Invoice = Invoice.objects.create(
            account=account,
            invoice_number="INV-1234",
            billing_service_invoice_id=None,
            issue_date=date,
            due_date=due_date,
            amount=total,
            paid=0,
            due=0,
        )
        return invoice

    def email_invoice(self, invoice: Invoice) -> None:
        return
