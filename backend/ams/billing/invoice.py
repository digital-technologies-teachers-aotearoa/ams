import logging
import re
from functools import partial
from typing import Optional

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ams.users.forms import format_membership_option_description
from ams.users.models import MembershipOption

from .models import Account, Invoice
from .service import BillingService, get_billing_service

logger = logging.getLogger(__name__)


class BillingException(Exception):
    pass


class BillingDetailUpdateException(BillingException):
    pass


class BillingInvoiceException(BillingException):
    pass


def email_invoice(billing_service: BillingService, invoice: Invoice) -> None:
    billing_service.email_invoice(invoice)


def can_send_email(email: str) -> bool:
    if not settings.BILLING_EMAIL_WHITELIST_REGEX or re.search(settings.BILLING_EMAIL_WHITELIST_REGEX, email):
        return True

    return False


def create_membership_option_invoice(account: Account, membership_option: MembershipOption) -> Optional[Invoice]:
    billing_service = get_billing_service()
    if not billing_service:
        return None

    # Don't create an invoice if the membership is free. Admin will need to approve membership manually
    if membership_option.cost == 0:
        return None

    try:
        if account.user_id:
            email = account.user.email
            billing_service.update_user_billing_details(account.user)
        else:
            email = account.organisation.email
            billing_service.update_organisation_billing_details(account.organisation)

    except Exception as e:
        logger.error(f"Error updating account {account.pk} billing details: {e}")
        raise BillingDetailUpdateException(e)

    try:
        invoice_line_items = [
            {
                "description": str(format_membership_option_description(membership_option)),
                "unit_amount": membership_option.cost,
                "quantity": 1,
            }
        ]

        issue_date = timezone.localdate()
        due_date = issue_date + relativedelta(months=1)

        invoice = billing_service.create_invoice(account, issue_date, due_date, invoice_line_items)

        if can_send_email(email):
            transaction.on_commit(partial(email_invoice, billing_service=billing_service, invoice=invoice))

    except Exception as e:
        logger.error(f"Error creating invoice for account {account.pk}: {e}")
        raise BillingInvoiceException(e)

    return invoice
