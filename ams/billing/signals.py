"""Django signals for billing domain.

Handles membership approval when an invoice transitions to paid.

We use a signal instead of overriding ``Invoice.save`` so the billing
service layer can live in ``ams.billing.services`` without forcing a
runtime import of that package inside ``models.py``. This eliminates the
previous circular import between the invoice model and membership
billing service, keeps model definitions lightweight, and centralises
side-effect orchestration here.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.billing.models import Invoice
from ams.billing.services.membership import MembershipBillingService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invoice)
def approve_memberships_on_invoice_payment(
    sender: type[Invoice],
    instance: Invoice,
    created: bool,  # noqa: FBT001 - Django signal signature requires positional boolean
    **_: Any,
) -> None:
    """Approve memberships when an existing invoice gains a paid_date.

    We only act when the invoice is updated (not newly created) and has a
    paid_date set. The service encapsulates the approval logic.
    """
    if created or not instance.paid_date:
        return
    try:
        MembershipBillingService().approve_paid_memberships(instance)
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "Failed approving memberships for invoice %s",
            instance.invoice_number,
        )
