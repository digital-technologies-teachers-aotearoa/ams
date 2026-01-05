from datetime import date
from datetime import timedelta
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ams.billing.services.membership import MembershipBillingService
from ams.billing.tests.factories import AccountFactory
from ams.memberships.tests.factories import MembershipOptionFactory

pytestmark = pytest.mark.django_db


class TestMembershipBillingServiceInvoiceDueDate:
    """Test invoice due date calculation using membership_option.invoice_due_days."""

    @patch("ams.billing.services.membership.timezone.localdate")
    @patch("ams.billing.services.membership.get_billing_service")
    def test_create_invoice_uses_invoice_due_days(
        self,
        mock_get_billing,
        mock_localdate,
    ):
        """Test that invoice due date is calculated using
        membership_option.invoice_due_days."""
        # Arrange
        test_date = date(2024, 1, 15)
        mock_localdate.return_value = test_date

        mock_billing = Mock()
        mock_invoice = Mock()
        mock_billing.create_invoice.return_value = mock_invoice
        mock_billing.update_user_billing_details = Mock()
        mock_get_billing.return_value = mock_billing

        account = AccountFactory(user_account=True)
        membership_option = MembershipOptionFactory(
            cost=100,
            invoice_due_days=45,  # Custom value
        )

        service = MembershipBillingService(billing_service=mock_billing)

        # Act
        service.create_membership_invoice(account, membership_option)

        # Assert
        call_args = mock_billing.create_invoice.call_args
        issue_date = call_args[0][1]
        due_date = call_args[0][2]

        expected_issue_date = test_date
        expected_due_date = test_date + timedelta(days=45)

        assert issue_date == expected_issue_date
        assert due_date == expected_due_date

    @patch("ams.billing.services.membership.timezone.localdate")
    @patch("ams.billing.services.membership.get_billing_service")
    def test_create_invoice_default_60_days(
        self,
        mock_get_billing,
        mock_localdate,
    ):
        """Test that invoice due date defaults to 60 days."""
        # Arrange
        test_date = date(2024, 3, 10)
        mock_localdate.return_value = test_date

        mock_billing = Mock()
        mock_invoice = Mock()
        mock_billing.create_invoice.return_value = mock_invoice
        mock_billing.update_user_billing_details = Mock()
        mock_get_billing.return_value = mock_billing

        account = AccountFactory(user_account=True)
        # Use default invoice_due_days (60)
        membership_option = MembershipOptionFactory(cost=100)

        service = MembershipBillingService(billing_service=mock_billing)

        # Act
        service.create_membership_invoice(account, membership_option)

        # Assert
        call_args = mock_billing.create_invoice.call_args
        issue_date = call_args[0][1]
        due_date = call_args[0][2]

        expected_issue_date = test_date
        expected_due_date = test_date + timedelta(days=60)

        assert issue_date == expected_issue_date
        assert due_date == expected_due_date

    @patch("ams.billing.services.membership.timezone.localdate")
    @patch("ams.billing.services.membership.get_billing_service")
    def test_create_invoice_with_custom_30_days(
        self,
        mock_get_billing,
        mock_localdate,
    ):
        """Test that invoice due date respects custom 30 day setting."""
        # Arrange
        test_date = date(2024, 6, 1)
        mock_localdate.return_value = test_date

        mock_billing = Mock()
        mock_invoice = Mock()
        mock_billing.create_invoice.return_value = mock_invoice
        mock_billing.update_user_billing_details = Mock()
        mock_get_billing.return_value = mock_billing

        account = AccountFactory(user_account=True)
        membership_option = MembershipOptionFactory(
            cost=75,
            invoice_due_days=30,
        )

        service = MembershipBillingService(billing_service=mock_billing)

        # Act
        service.create_membership_invoice(account, membership_option)

        # Assert
        call_args = mock_billing.create_invoice.call_args
        due_date = call_args[0][2]

        expected_due_date = test_date + timedelta(days=30)
        assert due_date == expected_due_date
