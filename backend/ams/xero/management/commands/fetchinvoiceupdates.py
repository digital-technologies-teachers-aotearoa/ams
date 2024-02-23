from typing import Any

from django.core.management.base import BaseCommand

from ...views import fetch_updated_invoice_details


class Command(BaseCommand):
    help = "Fetch updates to invoices that have changed in Xero."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Fetching updates to invoices"))
        fetch_updated_invoice_details(raise_exception=True)
        self.stdout.write(self.style.SUCCESS("Done"))
