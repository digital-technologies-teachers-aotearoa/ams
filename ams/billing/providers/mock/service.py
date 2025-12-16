from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.core.mail import send_mail

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
        subject = f"Invoice {invoice.invoice_number}"
        message = (
            f"Dear {invoice.account.user.get_full_name()},\n\n"
            f"Your invoice {invoice.invoice_number} has been issued.\n"
            f"Issue Date: {invoice.issue_date}\n"
            f"Due Date: {invoice.due_date}\n"
            f"Amount Due: {invoice.due}\n\n"
            "Thank you."
        )
        recipient = [invoice.account.user.email]
        send_mail(
            subject,
            message,
            "billing@ams.local",
            recipient,
            fail_silently=True,
        )

    def get_invoice_url(self, invoice: Invoice) -> str | None:
        return
