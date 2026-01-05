import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ams.billing.models import Account
from ams.billing.models import Invoice

pytestmark = pytest.mark.django_db


def _create_invoice_for_account(account):
    return Invoice.objects.create(
        account=account,
        invoice_number="INV-1234",
        issue_date=timezone.localdate(),
        due_date=timezone.localdate() + relativedelta(months=1),
        amount=100,
        due=100,
        paid=0,
    )


def test_paying_invoice_approves_pending_individual_membership(
    individual_membership_pending,
    user,
):
    individual_membership = individual_membership_pending
    account = Account.objects.create(user=individual_membership.user)
    invoice = _create_invoice_for_account(account)
    invoice.individual_membership = individual_membership
    invoice.save()

    invoice.paid_date = timezone.localdate()
    invoice.save()

    individual_membership.refresh_from_db()
    assert individual_membership.approved_datetime is not None


def test_paying_invoice_approves_individual_membership_of_unverified_user(
    individual_membership_pending,
):
    individual_membership = individual_membership_pending
    individual_membership.user.is_active = False
    individual_membership.user.save()
    account = Account.objects.create(user=individual_membership.user)
    invoice = _create_invoice_for_account(account)
    invoice.individual_membership = individual_membership
    invoice.save()

    invoice.paid_date = timezone.localdate()
    invoice.save()

    individual_membership.refresh_from_db()
    assert individual_membership.approved_datetime is not None


def test_paying_invoice_does_not_approve_cancelled_individual_membership(
    individual_membership_cancelled,
):
    individual_membership = individual_membership_cancelled
    # Ensure approved_datetime not set
    individual_membership.approved_datetime = None
    individual_membership.save()
    account = Account.objects.create(user=individual_membership.user)
    invoice = _create_invoice_for_account(account)
    individual_membership.invoice = invoice
    individual_membership.save()

    invoice.paid_date = timezone.localdate()
    invoice.save()

    individual_membership.refresh_from_db()
    assert individual_membership.approved_datetime is None


def test_paying_invoice_of_organisation_membership(organisation_membership):
    account = Account.objects.create(
        organisation=organisation_membership.organisation,
    )
    invoice = _create_invoice_for_account(account)
    organisation_membership.invoice = invoice
    organisation_membership.save()

    invoice.paid_date = timezone.localdate()
    invoice.save()

    organisation_membership.refresh_from_db()
