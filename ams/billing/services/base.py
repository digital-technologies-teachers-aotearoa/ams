from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from django.utils.module_loading import import_string

if TYPE_CHECKING:  # pragma: no cover
    from datetime import date

    from django.contrib.auth.models import User

    from ams.billing.models import Account
    from ams.billing.models import Invoice
    from ams.users.models import Organisation

# NOTE: We intentionally avoid importing heavy application models when not type checking
# to reduce risk of circular imports and lower import overhead.


class BillingService(ABC):
    """Abstract base class for billing service implementations."""

    @abstractmethod
    def update_user_billing_details(
        self,
        user: User,
    ) -> None:  # pragma: no cover - interface
        """Update billing details for a user."""
        ...

    @abstractmethod
    def update_organisation_billing_details(
        self,
        organisation: Organisation,
    ) -> None:  # pragma: no cover - interface
        """Update billing details for an organisation."""
        ...

    @abstractmethod
    def create_invoice(
        self,
        account: Account,
        date: date,
        due_date: date,
        line_items: list[dict[str, Any]],
        reference: str,
    ) -> Invoice:
        """Create an invoice in the billing system."""
        ...

    @abstractmethod
    def email_invoice(
        self,
        invoice: Invoice,
    ) -> None:  # pragma: no cover - interface
        """Send invoice via email."""
        ...


def get_billing_service() -> BillingService | None:
    """Return configured billing service instance or None if not set.

    Available providers:
    - ams.billing.providers.mock.MockBillingService
    - ams.billing.providers.xero.XeroBillingService
    - ams.billing.providers.xero.MockXeroBillingService
    """
    if getattr(settings, "BILLING_SERVICE_CLASS", None):
        service_class = import_string(settings.BILLING_SERVICE_CLASS)
        billing_service: BillingService = service_class()
        return billing_service
    return None
