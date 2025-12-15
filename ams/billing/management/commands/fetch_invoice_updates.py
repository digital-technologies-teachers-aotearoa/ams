from typing import Any

from django.core.management.base import BaseCommand

from ams.billing.providers.mock.service import MockBillingService
from ams.billing.providers.xero import fetch_updated_invoice_details
from ams.billing.providers.xero.service import MockXeroBillingService
from ams.billing.providers.xero.service import XeroBillingService
from ams.billing.services import BillingService
from ams.billing.services import get_billing_service


class Command(BaseCommand):
    help = "Fetch updates to invoices that have changed in the billing provider."

    def handle(self, *args: Any, **options: Any) -> None:
        billing_service: BillingService | None = get_billing_service()

        if not billing_service:
            self.stdout.write(
                self.style.ERROR("No billing service configured."),
            )
        elif isinstance(billing_service, (MockBillingService, MockXeroBillingService)):
            self.stdout.write(
                self.style.WARNING("No invoice updates to fetch with mock billing."),
            )
            self.stdout.write(self.style.SUCCESS("Done"))
        elif isinstance(billing_service, XeroBillingService):
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    "Fetching updates to invoices for Xero billing...",
                ),
            )
            result = fetch_updated_invoice_details(raise_exception=True)
            if result["updated_count"] > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated {result['updated_count']} invoice(s):",
                    ),
                )
                for invoice_number in result["invoice_numbers"]:
                    self.stdout.write(f"  - {invoice_number}")
            else:
                self.stdout.write(
                    self.style.SUCCESS("No invoices needed updating"),
                )
            self.stdout.write(self.style.SUCCESS("Done"))
        else:
            self.stdout.write(
                self.style.ERROR("Unknown billing service configured."),
            )
