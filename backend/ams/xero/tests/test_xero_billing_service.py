from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from xero_python.accounting import CurrencyCode
from xero_python.accounting import Invoice as AccountingInvoice
from xero_python.accounting import LineAmountTypes

from ams.billing.models import Account, Invoice
from ams.test.utils import any_organisation, any_user

if "ams.xero" not in settings.INSTALLED_APPS:
    pytest.skip(reason="ams.xero not in INSTALLED_APPS", allow_module_level=True)
else:
    from ..models import XeroContact
    from ..service import MockXeroBillingService


@override_settings(XERO_CURRENCY_CODE="NZD", XERO_ACCOUNT_CODE="200", XERO_AMOUNT_TYPE="INCLUSIVE")
class XeroBillingServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = any_user()
        self.user.account = Account.objects.create(user=self.user)
        self.user.save()

        self.organisation = any_organisation()
        self.organisation.account = Account.objects.create(organisation=self.organisation)
        self.organisation.save()

        self.billing_service = MockXeroBillingService()

    @patch("ams.xero.service.MockXeroBillingService._create_xero_contact")
    def test_should_create_expected_user_xero_contact(self, mock__create_xero_contact: Mock) -> None:
        # Given
        contact_id = "fake-new-contact-id"
        mock__create_xero_contact.return_value = contact_id

        # When
        self.billing_service.update_user_billing_details(self.user)

        # Then
        xero_contact = XeroContact.objects.get()

        expected_contact_params = {
            "name": self.user.get_full_name() + f" ({self.user.account.id})",
            "account_number": str(self.user.account.id),
            "email_address": self.user.email,
        }

        mock__create_xero_contact.assert_called_with(expected_contact_params)

        self.assertEqual(xero_contact.account, self.user.account)
        self.assertEqual(xero_contact.contact_id, contact_id)

    @patch("ams.xero.service.MockXeroBillingService._update_xero_contact")
    def test_should_update_users_billing_details(self, mock__update_xero_contact: Mock) -> None:
        # Given
        contact_id = "fake-existing-contact-id"
        XeroContact.objects.create(account=self.user.account, contact_id=contact_id)

        # When
        self.billing_service.update_user_billing_details(self.user)

        # Then
        expected_contact_params = {
            "name": self.user.get_full_name() + f" ({self.user.account.id})",
            "account_number": str(self.user.account.id),
            "email_address": self.user.email,
        }

        mock__update_xero_contact.assert_called_with(contact_id, expected_contact_params)

    @patch("ams.xero.service.MockXeroBillingService._create_xero_contact")
    def test_should_create_expected_organisation_xero_contact(self, mock__create_xero_contact: Mock) -> None:
        # Given
        contact_id = "fake-new-contact-id"
        mock__create_xero_contact.return_value = contact_id

        # When
        self.billing_service.update_organisation_billing_details(self.organisation)

        # Then
        xero_contact = XeroContact.objects.get()

        expected_contact_params = {
            "name": self.organisation.name + f" ({self.organisation.account.id})",
            "account_number": str(self.organisation.account.id),
            "email_address": self.organisation.email,
        }

        mock__create_xero_contact.assert_called_with(expected_contact_params)

        self.assertEqual(xero_contact.account, self.organisation.account)
        self.assertEqual(xero_contact.contact_id, contact_id)

    @patch("ams.xero.service.MockXeroBillingService._update_xero_contact")
    def test_should_update_organisations_billing_details(self, mock__update_xero_contact: Mock) -> None:
        # Given
        contact_id = "fake-existing-contact-id"
        XeroContact.objects.create(account=self.organisation.account, contact_id=contact_id)

        # When
        self.billing_service.update_organisation_billing_details(self.organisation)

        # Then
        expected_contact_params = {
            "name": self.organisation.name + f" ({self.organisation.account.id})",
            "account_number": str(self.organisation.account.id),
            "email_address": self.organisation.email,
        }

        mock__update_xero_contact.assert_called_with(contact_id, expected_contact_params)

    @patch("ams.xero.service.MockXeroBillingService._create_xero_invoice")
    def test_should_call_create_xero_invoice_with_expected_details(self, mock__create_xero_invoice: Mock) -> None:
        # Given
        account = self.user.account
        contact_id = "fake-existing-contact-id"
        XeroContact.objects.create(account=account, contact_id=contact_id)
        line_items = [{"description": "any description", "unit_amount": Decimal("123.45"), "quantity": 1}]
        issue_date = timezone.localdate()
        due_date = issue_date + relativedelta(months=1)

        mock__create_xero_invoice.return_value = AccountingInvoice(
            invoice_number="INV-1234",
            date=str(issue_date),
            due_date=str(due_date),
            total=line_items[0]["unit_amount"],
            amount_due=line_items[0]["unit_amount"],
            amount_paid=0,
        )

        # When
        self.billing_service.create_invoice(account, issue_date, due_date, line_items)

        # Then
        expected_invoice_details = {
            "date": issue_date,
            "due_date": due_date,
            "type": "ACCREC",
            "status": "AUTHORISED",
            "reference": str(self.user.account.pk),
            "currency_code": CurrencyCode[settings.XERO_CURRENCY_CODE],
            "line_amount_types": LineAmountTypes[settings.XERO_AMOUNT_TYPE],
        }
        expected_line_item_details = [
            {
                "description": line_item["description"],
                "unit_amount": line_item["unit_amount"],
                "account_code": settings.XERO_ACCOUNT_CODE,
                "quantity": 1,
            }
            for line_item in line_items
        ]
        mock__create_xero_invoice.assert_called_with(contact_id, expected_invoice_details, expected_line_item_details)

    def test_should_create_expected_invoice_record(self) -> None:
        # Given
        account = self.user.account
        contact_id = "fake-existing-contact-id"
        XeroContact.objects.create(account=account, contact_id=contact_id)
        line_items = [{"description": "any description", "unit_amount": Decimal("123.45"), "quantity": 1}]
        issue_date = timezone.localdate()
        due_date = issue_date + relativedelta(months=1)

        # When
        self.billing_service.create_invoice(account, issue_date, due_date, line_items)

        # Then
        invoice = Invoice.objects.get()

        self.assertEqual(invoice.billing_service_invoice_id, "e576f965-f2fb-459f-9ea8-035424ae31d7")
        self.assertEqual(invoice.invoice_number, "INV-1234")
        self.assertEqual(invoice.account, self.user.account)
        self.assertEqual(invoice.issue_date, issue_date)
        self.assertEqual(invoice.due_date, due_date)
        self.assertEqual(invoice.amount, line_items[0]["unit_amount"])
        self.assertEqual(invoice.due, line_items[0]["unit_amount"])
        self.assertEqual(invoice.paid, Decimal("0"))
