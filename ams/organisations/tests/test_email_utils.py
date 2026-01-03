"""Tests for organisation email utilities."""

from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.email_utils import send_staff_organisation_created_notification
from ams.organisations.email_utils import (
    send_staff_organisation_membership_notification,
)
from ams.organisations.tests.factories import OrganisationFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestSendStaffOrganisationCreatedNotification:
    """Tests for send_staff_organisation_created_notification function."""

    def test_send_notification_success(self, mailoutbox):
        """Test that notification is sent successfully to all staff users."""
        # Create staff users
        staff1 = UserFactory(is_staff=True, email="staff1@example.com")
        staff2 = UserFactory(is_staff=True, email="staff2@example.com")

        # Create organisation and creator
        creator = UserFactory(
            email="creator@example.com",
            first_name="John",
            last_name="Doe",
        )
        organisation = OrganisationFactory(name="Test Organisation")

        # Send notification
        send_staff_organisation_created_notification(organisation, creator)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check recipients
        assert set(email.to) == {staff1.email, staff2.email}

        # Check subject
        assert "Test Organisation" in email.subject
        assert "New Organisation Created" in email.subject

        # Check body contains organisation details
        assert organisation.name in email.body
        assert creator.email in email.body

    @override_settings(NOTIFY_STAFF_ORG_EVENTS=False)
    def test_notification_disabled(self, mailoutbox):
        """Test that notification is not sent when feature flag is disabled."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation and creator
        creator = UserFactory(email="creator@example.com")
        organisation = OrganisationFactory()

        # Send notification
        send_staff_organisation_created_notification(organisation, creator)

        # Assert no email was sent
        assert len(mailoutbox) == 0

    def test_no_staff_users(self, mailoutbox):
        """Test that no email is sent when there are no staff users."""
        # Ensure no staff users exist
        User.objects.filter(is_staff=True).delete()

        # Create organisation and creator
        creator = UserFactory(email="creator@example.com")
        organisation = OrganisationFactory()

        # Send notification (should not raise exception)
        send_staff_organisation_created_notification(organisation, creator)

        # Assert no email was sent
        assert len(mailoutbox) == 0

    @patch("ams.organisations.email_utils.send_mail")
    @patch("ams.organisations.email_utils.logger")
    def test_email_failure_graceful_handling(self, mock_logger, mock_send_mail):
        """Test that email failures are handled gracefully without raising."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation and creator
        creator = UserFactory(email="creator@example.com")
        organisation = OrganisationFactory()

        # Mock send_mail to raise exception
        mock_send_mail.side_effect = SMTPException("SMTP server error")

        # Send notification (should not raise exception)
        send_staff_organisation_created_notification(organisation, creator)

        # Assert logger.exception was called
        assert mock_logger.exception.called

    def test_creator_without_full_name(self, mailoutbox):
        """Test notification when creator has no full name (uses username)."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create creator without first/last name
        creator = UserFactory(
            email="creator@example.com",
            username="creator123",
            first_name="",
            last_name="",
        )
        organisation = OrganisationFactory()

        # Send notification
        send_staff_organisation_created_notification(organisation, creator)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that username is used
        assert "creator123" in email.body


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
            max_seats=10,
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

    @override_settings(NOTIFY_STAFF_ORG_EVENTS=False)
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
            invoice=None,
        )

        # Send notification
        send_staff_organisation_membership_notification(membership)

        # Assert email was sent
        assert len(mailoutbox) == 1
        # Email should not crash due to missing invoice

    @patch("ams.organisations.email_utils.send_mail")
    @patch("ams.organisations.email_utils.logger")
    def test_email_failure_graceful_handling(self, mock_logger, mock_send_mail):
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

        # Mock send_mail to raise exception
        mock_send_mail.side_effect = SMTPException("SMTP server error")

        # Send notification (should not raise exception)
        send_staff_organisation_membership_notification(membership)

        # Assert logger.exception was called
        assert mock_logger.exception.called
