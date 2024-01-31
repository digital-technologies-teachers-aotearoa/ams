from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.test import TestCase

from ams.billing.models import Account
from ams.test.utils import any_organisation, any_user

if "ams.xero" not in settings.INSTALLED_APPS:
    pytest.skip(reason="ams.xero not in INSTALLED_APPS", allow_module_level=True)
else:
    from ..models import XeroContact
    from ..service import MockXeroBillingService


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
