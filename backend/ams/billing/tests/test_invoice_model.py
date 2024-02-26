from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from ams.test.utils import any_organisation_membership, any_user_membership

from ..models import Account, Invoice


class InvoiceModelTests(TestCase):
    def test_paying_invoice_approves_pending_user_membership(self) -> None:
        # Given
        user_membership = any_user_membership()
        user_membership.approved_datetime = None
        user_membership.save()

        account = Account.objects.create(user=user_membership.user)

        invoice = Invoice.objects.create(
            account=account,
            invoice_number="INV-1234",
            issue_date=timezone.localdate(),
            due_date=timezone.localdate() + relativedelta(months=1),
            amount=100,
            due=100,
            paid=0,
        )
        user_membership.invoice = invoice
        user_membership.save()

        # When
        invoice.paid_date = timezone.localdate()
        invoice.save()

        # Then
        user_membership.refresh_from_db()
        self.assertIsNotNone(user_membership.approved_datetime)

    def test_paying_invoice_approves_user_membership_of_unverified_user(self) -> None:
        # Given a user may pay the invoice before verifying their email (making them active)
        user_membership = any_user_membership()
        user_membership.approved_datetime = None
        user_membership.save()

        user_membership.user.is_active = False
        user_membership.user.save()

        account = Account.objects.create(user=user_membership.user)

        invoice = Invoice.objects.create(
            account=account,
            invoice_number="INV-1234",
            issue_date=timezone.localdate(),
            due_date=timezone.localdate() + relativedelta(months=1),
            amount=100,
            due=100,
            paid=0,
        )
        user_membership.invoice = invoice
        user_membership.save()

        # When
        invoice.paid_date = timezone.localdate()
        invoice.save()

        # Then
        user_membership.refresh_from_db()
        self.assertIsNotNone(user_membership.approved_datetime)

    def test_paying_invoice_does_not_approve_cancelled_user_membership(self) -> None:
        # Given
        user_membership = any_user_membership()
        user_membership.approved_datetime = None
        user_membership.cancelled_datetime = timezone.localtime()
        user_membership.save()

        account = Account.objects.create(user=user_membership.user)

        invoice = Invoice.objects.create(
            account=account,
            invoice_number="INV-1234",
            issue_date=timezone.localdate(),
            due_date=timezone.localdate() + relativedelta(months=1),
            amount=100,
            due=100,
            paid=0,
        )
        user_membership.invoice = invoice
        user_membership.save()

        # When
        invoice.paid_date = timezone.localdate()
        invoice.save()

        # Then
        user_membership.refresh_from_db()
        self.assertIsNone(user_membership.approved_datetime)

    def test_paying_invoice_of_organisation_membership(self) -> None:
        # Given
        organisation_membership = any_organisation_membership()
        account = Account.objects.create(organisation=organisation_membership.organisation)

        invoice = Invoice.objects.create(
            account=account,
            invoice_number="INV-1234",
            issue_date=timezone.localdate(),
            due_date=timezone.localdate() + relativedelta(months=1),
            amount=100,
            due=100,
            paid=0,
        )

        organisation_membership.invoice = invoice
        organisation_membership.save()

        # When
        invoice.paid_date = timezone.localdate()
        invoice.save()

        # Just testing it works - organisation memberships don't require approval currently
        organisation_membership.refresh_from_db()
