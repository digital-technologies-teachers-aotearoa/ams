from typing import Any

from django.core.management.base import BaseCommand

from ams.billing.providers.xero import fetch_updated_invoice_details


class Command(BaseCommand):
    help = "Fetch updates to invoices that have changed in the billing provider."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "provider_name",
            help="Name of the provider whose invoices should be updated",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        provider_name = options["provider_name"]
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Fetching updates to invoices for {provider_name} billing...",
            ),
        )
        if provider_name.lower() == "xero":
            fetch_updated_invoice_details(raise_exception=True)
        elif provider_name.lower() == "mock":
            self.stdout.write(
                self.style.WARNING("No invoice updates to fetch with mock billing."),
            )
        self.stdout.write(self.style.SUCCESS("Done"))
