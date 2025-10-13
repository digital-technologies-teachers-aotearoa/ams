import logging
import re
from functools import partial

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ams.billing.exceptions import BillingDetailUpdateError
from ams.billing.exceptions import BillingInvoiceError
from ams.billing.models import Invoice
from ams.billing.services import BillingService
from ams.billing.services import get_billing_service

logger = logging.getLogger(__name__)


def email_invoice(billing_service: BillingService, invoice) -> None:
    billing_service.email_invoice(invoice)


def can_send_email(email: str) -> bool:
    return bool(
        not settings.BILLING_EMAIL_WHITELIST_REGEX
        or re.search(settings.BILLING_EMAIL_WHITELIST_REGEX, email),
    )


def create_membership_option_invoice(account, membership_option) -> Invoice | None:
    billing_service = get_billing_service()
    if not billing_service:
        return None

    # Don't create an invoice if the membership is free.
    # Admin will need to approve membership manually
    if membership_option.cost == 0:
        return None

    try:
        if account.user_id:
            email = account.user.email
            billing_service.update_user_billing_details(account.user)
        else:
            email = account.organisation.email
            billing_service.update_organisation_billing_details(account.organisation)

    except Exception as e:  # broad catch to wrap in domain error
        logger.exception(
            "Error updating account %s billing details",
            account.pk,
        )
        raise BillingDetailUpdateError(e) from e

    try:
        invoice_line_items = [
            {
                "description": str(membership_option),
                "unit_amount": membership_option.cost,
                "quantity": 1,
            },
        ]

        issue_date = timezone.localdate()
        due_date = issue_date + relativedelta(months=1)

        invoice = billing_service.create_invoice(
            account,
            issue_date,
            due_date,
            invoice_line_items,
        )

        if can_send_email(email):
            transaction.on_commit(
                partial(
                    email_invoice,
                    billing_service=billing_service,
                    invoice=invoice,
                ),
            )

    except Exception as e:  # broad catch to wrap in domain error
        logger.exception(
            "Error creating invoice for account %s",
            account.pk,
        )
        raise BillingInvoiceError(e) from e

    return invoice
