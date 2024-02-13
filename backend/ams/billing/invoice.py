from sys import stderr

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ams.users.forms import format_membership_option_description
from ams.users.models import MembershipOption

from .models import Account
from .service import get_billing_service


class BillingException(Exception):
    pass


class BillingDetailUpdateException(BillingException):
    pass


class BillingInvoiceException(BillingException):
    pass


def create_membership_option_invoice(account: Account, membership_option: MembershipOption) -> None:
    billing_service = get_billing_service()
    if not billing_service:
        return

    try:
        if account.user_id:
            billing_service.update_user_billing_details(account.user)
        else:
            billing_service.update_organisation_billing_details(account.organisation)

    except Exception as e:
        print(f"Error updating account {account.pk} billing details: {e}", file=stderr)
        raise BillingDetailUpdateException(e)

    try:
        invoice_line_items = [
            {
                "description": str(format_membership_option_description(membership_option)),
                "unit_amount": membership_option.cost,
                "quantity": 1,
            }
        ]

        issue_date = timezone.localtime()
        due_date = issue_date + relativedelta(months=1)

        billing_service.create_invoice(account, issue_date, due_date, invoice_line_items)

    except Exception as e:
        print(f"Error creating invoice for account {account.pk}: {e}", file=stderr)
        raise BillingInvoiceException(e)
