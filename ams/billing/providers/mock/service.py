from datetime import date
from typing import Any

from django.contrib.auth.models import User

from ams.billing.models import Account
from ams.billing.models import Invoice
from ams.billing.services import BillingService
from ams.memberships.models import Organisation
from ams.utils.email import send_templated_email


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
        reference: str,
    ) -> Invoice:
        total = 0
        for line_item in line_items:
            total += line_item["unit_amount"] * line_item["quantity"]

        invoice_number = f"MOCK-{Invoice.objects.count() + 1}"
        invoice: Invoice = Invoice.objects.create(
            account=account,
            invoice_number=invoice_number,
            billing_service_invoice_id=invoice_number,
            issue_date=date,
            due_date=due_date,
            amount=total,
            paid=0,
            due=total,
        )
        return invoice

    def email_invoice(self, invoice: Invoice) -> None:
        send_templated_email(
            subject=f"Invoice {invoice.invoice_number}",
            template_name="billing/emails/mock_invoice",
            context={
                "invoice": invoice,
                "account": invoice.account,
                "user_name": invoice.account.user.get_full_name(),
            },
            recipient_list=[invoice.account.user.email],
            from_email="billing@ams.local",
            fail_silently=True,
        )

    def get_invoice_url(self, invoice: Invoice) -> str | None:
        return
