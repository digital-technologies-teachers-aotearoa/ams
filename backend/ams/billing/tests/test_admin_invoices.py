from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ams.billing.models import Account, Invoice
from ams.test.utils import any_organisation, any_user, parse_response_table_rows


class AdminInvoiceListTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(username="testadminuser", is_staff=True)
        self.url = "/billing/invoices/"

        self.user = any_user()
        self.organisation = any_organisation()

        Account.objects.create(user=self.user)
        Account.objects.create(organisation=self.organisation)

        issue_date = timezone.localtime()
        due_date = issue_date + relativedelta(months=1)

        self.user_invoice = Invoice.objects.create(
            account=self.user.account,
            invoice_number="INV-0001",
            issue_date=issue_date.date(),
            due_date=due_date.date(),
            amount=Decimal("100.00"),
            paid=Decimal("0.00"),
            due=Decimal("100.00"),
        )

        self.organisation_invoice = Invoice.objects.create(
            account=self.organisation.account,
            invoice_number="INV-0002",
            issue_date=issue_date.date(),
            due_date=due_date.date(),
            amount=Decimal("200.00"),
            paid=Decimal("50.00"),
            due=Decimal("150.00"),
        )

        self.client.force_login(self.admin_user)

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin_invoices.html")

    def test_should_show_expected_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["invoice_number", "to", "type", "issue_date", "due_date", "amount", "paid", "due"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["Invoice Number", "To", "Type", "Issue Date", "Due Date", "Amount", "Paid", "Due"]
        columns = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.organisation_invoice.invoice_number,
                self.organisation.name,
                "Organisation",
                date_format(self.organisation_invoice.issue_date, format="SHORT_DATE_FORMAT"),
                date_format(self.organisation_invoice.due_date, format="SHORT_DATE_FORMAT"),
                self.organisation_invoice.amount,
                self.organisation_invoice.paid,
                self.organisation_invoice.due,
            ],
            [
                self.user_invoice.invoice_number,
                self.user.username,
                "User",
                date_format(self.user_invoice.issue_date, format="SHORT_DATE_FORMAT"),
                date_format(self.user_invoice.due_date, format="SHORT_DATE_FORMAT"),
                self.user_invoice.amount,
                self.user_invoice.paid,
                self.user_invoice.due,
            ],
        ]

        self.assertListEqual(expected_rows, rows)
