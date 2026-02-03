"""Tests for organisation email utilities."""

from decimal import Decimal
from smtplib import SMTPException
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from ams.memberships.email_utils import send_staff_individual_membership_notification
from ams.memberships.email_utils import send_staff_organisation_membership_notification
from ams.memberships.email_utils import send_staff_organisation_seats_added_notification
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestSendStaffOrganisationMembershipNotification:
    """Tests for send_staff_organisation_membership_notification function."""

    def test_send_notification_success(self, mailoutbox):
        """Test that notification is sent successfully to all staff users."""
        # Create staff users
        staff1 = UserFactory(is_staff=True, email="staff1@example.com")
        staff2 = UserFactory(is_staff=True, email="staff2@example.com")

        # Create organisation membership
        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Annual Membership",
            cost=100,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=10,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate(),
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check recipients
        assert set(email.to) == {staff1.email, staff2.email}

        # Check subject
        assert "Test Org" in email.subject
        assert "New Organisation Membership" in email.subject

        # Check body contains membership details
        assert organisation.name in email.body
        assert "Annual Membership" in email.body

    @override_settings(NOTIFY_STAFF_MEMBERSHIP_EVENTS=False)
    def test_notification_disabled(self, mailoutbox):
        """Test that notification is not sent when feature flag is disabled."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_no_staff_users(self, mailoutbox):
        """Test that no email is sent when there are no staff users."""
        # Ensure no staff users exist
        User.objects.filter(is_staff=True).delete()

        # Create organisation membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Send notification (should not raise exception)
        send_staff_organisation_membership_notification(membership)

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_membership_without_invoice(self, mailoutbox):
        """Test notification when membership has no invoice."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation membership without invoice
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            cost=0,  # Zero-cost membership
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        # Email should not crash due to missing invoice

    @patch("ams.memberships.email_utils.send_templated_email")
    @patch("ams.memberships.email_utils.logger")
    def test_email_failure_graceful_handling(
        self,
        mock_logger,
        mock_send_templated_email,
    ):
        """Test that email failures are handled gracefully without raising."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Mock send_templated_email to raise exception
        mock_send_templated_email.side_effect = SMTPException("SMTP server error")

        # Send notification (should not raise exception)
        send_staff_organisation_membership_notification(membership)

        # Assert logger.exception was called
        assert mock_logger.exception.called


@pytest.mark.django_db
class TestSendStaffOrganisationSeatsAddedNotification:
    """Tests for send_staff_organisation_seats_added_notification function."""

    def test_send_notification_success(self, mailoutbox):
        """Test that notification is sent successfully to all staff users."""
        # Create staff users
        staff1 = UserFactory(is_staff=True, email="staff1@example.com")
        staff2 = UserFactory(is_staff=True, email="staff2@example.com")

        # Create organisation and membership
        organisation = OrganisationFactory(name="Test Organisation")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Annual Membership",
            cost=Decimal("1000.00"),
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=15,  # New total after adding 5 seats
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate(),
        )

        # Create mock invoice
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"

        # Send notification
        send_staff_organisation_seats_added_notification(
            organisation=organisation,
            membership=membership,
            seats_added=5,
            prorata_cost=Decimal("500.00"),
            invoice=mock_invoice,
        )

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check recipients
        assert set(email.to) == {staff1.email, staff2.email}

        # Check subject
        assert "Test Organisation" in email.subject
        assert "Seats Added" in email.subject

        # Check body contains seat details
        assert organisation.name in email.body
        assert "5" in email.body  # seats_added
        assert "15" in email.body  # new_total_seats
        assert "500.00" in email.body  # prorata_cost
        assert "INV-12345" in email.body  # invoice number

    @override_settings(NOTIFY_STAFF_MEMBERSHIP_EVENTS=False)
    def test_notification_disabled(self, mailoutbox):
        """Test that notification is not sent when feature flag is disabled."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation and membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Create mock invoice
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"

        # Send notification
        send_staff_organisation_seats_added_notification(
            organisation=organisation,
            membership=membership,
            seats_added=5,
            prorata_cost=Decimal("500.00"),
            invoice=mock_invoice,
        )

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_no_staff_users(self, mailoutbox):
        """Test that no email is sent when there are no staff users."""
        # Ensure no staff users exist
        User.objects.filter(is_staff=True).delete()

        # Create organisation and membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Create mock invoice
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"

        # Send notification (should not raise exception)
        send_staff_organisation_seats_added_notification(
            organisation=organisation,
            membership=membership,
            seats_added=5,
            prorata_cost=Decimal("500.00"),
            invoice=mock_invoice,
        )

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_notification_without_invoice(self, mailoutbox):
        """Test notification when no invoice is provided."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation and membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            cost=Decimal("0.00"),  # Free membership
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Send notification without invoice
        send_staff_organisation_seats_added_notification(
            organisation=organisation,
            membership=membership,
            seats_added=5,
            prorata_cost=Decimal("0.00"),
            invoice=None,
        )

        # Assert email was sent
        assert len(mailoutbox) == 1
        # Email should not crash due to missing invoice

    @patch("ams.memberships.email_utils.send_templated_email")
    @patch("ams.memberships.email_utils.logger")
    def test_email_failure_graceful_handling(
        self,
        mock_logger,
        mock_send_templated_email,
    ):
        """Test that email failures are handled gracefully without raising."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation and membership
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
        )

        # Create mock invoice
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"

        # Mock send_templated_email to raise exception
        mock_send_templated_email.side_effect = SMTPException("SMTP server error")

        # Send notification (should not raise exception)
        send_staff_organisation_seats_added_notification(
            organisation=organisation,
            membership=membership,
            seats_added=5,
            prorata_cost=Decimal("500.00"),
            invoice=mock_invoice,
        )

        # Assert logger.exception was called
        assert mock_logger.exception.called


@pytest.mark.django_db
class TestSendStaffIndividualMembershipNotification:
    """Tests for send_staff_individual_membership_notification function."""

    def test_send_notification_success(self, mailoutbox):
        """Test that notification is sent successfully to all staff users."""
        # Create staff users
        staff1 = UserFactory(is_staff=True, email="staff1@example.com")
        staff2 = UserFactory(is_staff=True, email="staff2@example.com")

        # Create individual membership
        user = UserFactory(first_name="John", last_name="Doe", email="john@example.com")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Annual Individual Membership",
            cost=100,
        )
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate(),
        )

        # Send notification
        send_staff_individual_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check recipients
        assert set(email.to) == {staff1.email, staff2.email}

        # Check subject
        assert "John Doe" in email.subject
        assert "New Individual Membership" in email.subject

        # Check body contains membership details
        assert "John Doe" in email.body
        assert "john@example.com" in email.body
        assert "Annual Individual Membership" in email.body

    @override_settings(NOTIFY_STAFF_MEMBERSHIP_EVENTS=False)
    def test_notification_disabled(self, mailoutbox):
        """Test that notification is not sent when feature flag is disabled."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create individual membership
        user = UserFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
        )
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
        )

        # Send notification
        send_staff_individual_membership_notification(membership)

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_no_staff_users(self, mailoutbox):
        """Test that no email is sent when there are no staff users."""
        # Ensure no staff users exist
        User.objects.filter(is_staff=True).delete()

        # Create individual membership
        user = UserFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
        )
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
        )

        # Send notification (should not raise exception)
        send_staff_individual_membership_notification(membership)

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_membership_without_invoice(self, mailoutbox):
        """Test notification when membership has no invoice."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create individual membership without invoice (zero-cost)
        user = UserFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            cost=0,  # Zero-cost membership
        )
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
        )

        # Send notification
        send_staff_individual_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        # Email should not crash due to missing invoice

    @patch("ams.memberships.email_utils.send_templated_email")
    @patch("ams.memberships.email_utils.logger")
    def test_email_failure_graceful_handling(
        self,
        mock_logger,
        mock_send_templated_email,
    ):
        """Test that email failures are handled gracefully without raising."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create individual membership
        user = UserFactory()
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
        )
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
        )

        # Mock send_templated_email to raise exception
        mock_send_templated_email.side_effect = SMTPException("SMTP server error")

        # Send notification (should not raise exception)
        send_staff_individual_membership_notification(membership)

        # Assert logger.exception was called
        assert mock_logger.exception.called


@pytest.mark.django_db
class TestEmailNotificationContextVariables:
    """Tests for requires_approval and is_free context variables in emails."""

    def test_individual_free_pending_context(self, mailoutbox):
        """Test individual free membership pending approval has correct context."""
        UserFactory(is_staff=True, email="staff@example.com")

        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Free Individual",
            cost=0,
        )
        user = UserFactory()
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            approved_datetime=None,  # Pending approval
        )

        send_staff_individual_membership_notification(membership)

        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that pending approval warning is in email
        assert "ACTION REQUIRED" in email.body
        assert "Pending Approval" in email.body

    def test_individual_free_approved_context(self, mailoutbox):
        """Test individual free membership approved has correct context."""
        UserFactory(is_staff=True, email="staff@example.com")

        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Free Individual",
            cost=0,
        )
        user = UserFactory()
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            approved_datetime=timezone.now(),  # Approved
        )

        send_staff_individual_membership_notification(membership)

        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Should show as approved, not pending
        assert "Approved" in email.body
        # Should not have ACTION REQUIRED warning
        assert "ACTION REQUIRED" not in email.body

    def test_individual_paid_pending_context(self, mailoutbox):
        """Test individual paid membership has correct context."""
        UserFactory(is_staff=True, email="staff@example.com")

        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Paid Individual",
            cost=99.99,
        )
        user = UserFactory()
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            approved_datetime=None,  # Pending payment
        )

        send_staff_individual_membership_notification(membership)

        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Paid memberships pending payment should show as pending
        assert "Pending Approval" in email.body
        # But should NOT show ACTION REQUIRED (not a free membership)
        assert "ACTION REQUIRED" not in email.body

    def test_organisation_free_pending_context(self, mailoutbox):
        """Test organisation free membership pending approval has correct context."""
        UserFactory(is_staff=True, email="staff@example.com")

        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Free Organisation",
            cost=0,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=None,  # Pending approval
        )

        send_staff_organisation_membership_notification(membership)

        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that pending approval warning is in email
        assert "ACTION REQUIRED" in email.body
        assert "Pending Approval" in email.body

    def test_organisation_free_approved_context(self, mailoutbox):
        """Test organisation free membership approved has correct context."""
        UserFactory(is_staff=True, email="staff@example.com")

        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Free Organisation",
            cost=0,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=timezone.now(),  # Approved
        )

        send_staff_organisation_membership_notification(membership)

        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Should show as approved, not pending
        assert "Approved" in email.body
        # Should not have ACTION REQUIRED warning
        assert "ACTION REQUIRED" not in email.body

    def test_organisation_paid_pending_context(self, mailoutbox):
        """Test organisation paid membership has correct context."""
        UserFactory(is_staff=True, email="staff@example.com")

        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Paid Organisation",
            cost=199.99,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=None,  # Pending payment
        )

        send_staff_organisation_membership_notification(membership)

        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Paid memberships pending payment should show as pending
        assert "Pending Approval" in email.body
        # But should NOT show ACTION REQUIRED (not a free membership)
        assert "ACTION REQUIRED" not in email.body


@pytest.mark.django_db
class TestEmailNotificationWhenNotificationsDisabled:
    """Tests for edge case where notifications are disabled but approval is required."""

    @override_settings(
        NOTIFY_STAFF_MEMBERSHIP_EVENTS=False,
        REQUIRE_FREE_MEMBERSHIP_APPROVAL=True,
    )
    def test_individual_free_pending_sends_email_despite_disabled_notifications(
        self,
        mailoutbox,
    ):
        """Test that free individual memberships requiring approval send email even
        when notifications disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Free Individual",
            cost=0,
        )
        user = UserFactory()
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            approved_datetime=None,  # Pending approval
        )

        send_staff_individual_membership_notification(membership)

        # Email SHOULD be sent despite notifications being disabled
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Subject should start with "REQUIRES APPROVAL"
        assert email.subject.startswith("REQUIRES APPROVAL")
        assert "ACTION REQUIRED" in email.body

    @override_settings(
        NOTIFY_STAFF_MEMBERSHIP_EVENTS=False,
        REQUIRE_FREE_MEMBERSHIP_APPROVAL=False,
    )
    def test_individual_free_approved_no_email_when_notifications_disabled(
        self,
        mailoutbox,
    ):
        """Test that auto-approved free memberships don't send email when
        notifications disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Free Individual",
            cost=0,
        )
        user = UserFactory()
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            approved_datetime=timezone.now(),  # Auto-approved
        )

        send_staff_individual_membership_notification(membership)

        # Email should NOT be sent (notifications disabled, no approval needed)
        assert len(mailoutbox) == 0

    @override_settings(NOTIFY_STAFF_MEMBERSHIP_EVENTS=False)
    def test_individual_paid_no_email_when_notifications_disabled(self, mailoutbox):
        """Test that paid memberships don't send email when notifications disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.INDIVIDUAL,
            name="Paid Individual",
            cost=99.99,
        )
        user = UserFactory()
        membership = IndividualMembershipFactory(
            user=user,
            membership_option=membership_option,
            approved_datetime=None,  # Pending payment
        )

        send_staff_individual_membership_notification(membership)

        # Email should NOT be sent
        # (notifications disabled, not a free membership approval)
        assert len(mailoutbox) == 0

    @override_settings(
        NOTIFY_STAFF_MEMBERSHIP_EVENTS=False,
        REQUIRE_FREE_MEMBERSHIP_APPROVAL=True,
    )
    def test_organisation_free_pending_sends_email_despite_disabled_notifications(
        self,
        mailoutbox,
    ):
        """Test that free org memberships requiring approval send email even when
        notifications disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Free Organisation",
            cost=0,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=None,  # Pending approval
        )

        send_staff_organisation_membership_notification(membership)

        # Email SHOULD be sent despite notifications being disabled
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Subject should start with "REQUIRES APPROVAL"
        assert email.subject.startswith("REQUIRES APPROVAL")
        assert "ACTION REQUIRED" in email.body

    @override_settings(
        NOTIFY_STAFF_MEMBERSHIP_EVENTS=False,
        REQUIRE_FREE_MEMBERSHIP_APPROVAL=False,
    )
    def test_organisation_free_approved_no_email_when_notifications_disabled(
        self,
        mailoutbox,
    ):
        """Test that auto-approved free org memberships don't send email when
        notifications disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Free Organisation",
            cost=0,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=timezone.now(),  # Auto-approved
        )

        send_staff_organisation_membership_notification(membership)

        # Email should NOT be sent (notifications disabled, no approval needed)
        assert len(mailoutbox) == 0

    @override_settings(NOTIFY_STAFF_MEMBERSHIP_EVENTS=False)
    def test_organisation_paid_no_email_when_notifications_disabled(self, mailoutbox):
        """Test that paid org memberships don't send email when notifications
        disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        organisation = OrganisationFactory(name="Test Org")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Paid Organisation",
            cost=199.99,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=None,  # Pending payment
        )

        send_staff_organisation_membership_notification(membership)

        # Email should NOT be sent
        # (notifications disabled, not a free membership approval)
        assert len(mailoutbox) == 0


@pytest.mark.django_db
class TestOrganisationMembershipEmailPricing:
    """Tests for organisation membership email pricing display."""

    def test_organisation_membership_displays_total_cost(self, mailoutbox):
        """Test that email displays total cost (seats x per-seat price)."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation membership: 5 seats at $100/seat
        organisation = OrganisationFactory(name="Test Organisation")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Standard Membership",
            cost=Decimal("100.00"),
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=timezone.now(),
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that total cost is displayed ($500)
        assert "$500" in email.body
        # Check that breakdown is shown
        assert "5" in email.body  # seats
        assert "$100" in email.body  # per-seat cost

    def test_organisation_membership_with_free_seats(self, mailoutbox):
        """Test that email correctly displays cost when some seats are free."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation membership option with max_charged_seats
        organisation = OrganisationFactory(name="Test Organisation")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Limited Charging Membership",
            cost=Decimal("100.00"),
            max_charged_seats=4,  # Only charge for 4 seats
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=6,  # 6 total seats, but only 4 charged
            approved_datetime=timezone.now(),
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that total cost is $400 (not $600)
        assert "$400" in email.body
        # Check that it mentions free seats
        assert "2 free seat" in email.body
        assert "4 charged seat" in email.body

    def test_organisation_membership_zero_cost(self, mailoutbox):
        """Test that email displays $0 cost correctly for free memberships."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create free organisation membership
        organisation = OrganisationFactory(name="Test Organisation")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Free Membership",
            cost=Decimal("0.00"),
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved_datetime=timezone.now(),
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that cost is displayed as $0
        assert "$0" in email.body
        # Should not crash or display errors

    def test_organisation_membership_single_seat(self, mailoutbox):
        """Test that email displays correctly for single seat (pluralization)."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation membership with single seat
        organisation = OrganisationFactory(name="Test Organisation")
        membership_option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            name="Single Seat Membership",
            cost=Decimal("150.00"),
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=1,
            approved_datetime=timezone.now(),
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that cost is displayed correctly
        assert "$150" in email.body
        # Check proper pluralization (should be "1 seat" not "1 seats")
        assert "1 seat" in email.body
