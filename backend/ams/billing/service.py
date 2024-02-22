from datetime import date
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.module_loading import import_string

from ams.users.models import Organisation

from .models import Account


class BillingService:
    def update_user_billing_details(self, user: User) -> None:
        raise NotImplementedError

    def update_organisation_billing_details(self, organisation: Organisation) -> None:
        raise NotImplementedError

    def create_invoice(self, account: Account, date: date, due_date: date, line_items: List[Dict[str, Any]]) -> None:
        raise NotImplementedError


class MockBillingService:
    def update_user_billing_details(self, user: User) -> None:
        return

    def update_organisation_billing_details(self, organisation: Organisation) -> None:
        return

    def create_invoice(self, account: Account, date: date, due_date: date, line_items: List[Dict[str, Any]]) -> None:
        return


def get_billing_service() -> Optional[BillingService]:
    if settings.BILLING_SERVICE_CLASS:
        service_class = import_string(settings.BILLING_SERVICE_CLASS)
        billing_service: BillingService = service_class()
        return billing_service

    return None
