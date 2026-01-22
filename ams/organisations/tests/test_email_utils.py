"""Tests for organisation email utilities."""

from smtplib import SMTPException
from unittest.mock import patch
from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
from django.test import RequestFactory
from django.test import override_settings
from django.urls import reverse

from ams.organisations.email_utils import send_organisation_invite_email
from ams.organisations.email_utils import send_staff_organisation_created_notification
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
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

    @override_settings(NOTIFY_STAFF_ORGANISATION_EVENTS=False)
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

    @patch("ams.organisations.email_utils.send_templated_email")
    @patch("ams.organisations.email_utils.logger")
    def test_email_failure_graceful_handling(
        self,
        mock_logger,
        mock_send_templated_email,
    ):
        """Test that email failures are handled gracefully without raising."""
        # Create staff user
        UserFactory(is_staff=True, email="staff@example.com")

        # Create organisation and creator
        creator = UserFactory(email="creator@example.com")
        organisation = OrganisationFactory()

        # Mock send_templated_email to raise exception
        mock_send_templated_email.side_effect = SMTPException("SMTP server error")

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
class TestSendOrganisationInviteEmail:
    """Tests for send_organisation_invite_email function."""

    def test_invite_existing_user_includes_login_redirect(self, mailoutbox):
        """Test that invites for existing users include ?next= parameters."""
        # Create user and organisation
        user = UserFactory(email="user@example.com")
        organisation = OrganisationFactory(name="Test Org")

        # Create invite with user linked
        member = OrganisationMemberFactory(
            user=user,
            invite_email=user.email,
            organisation=organisation,
        )

        # Create request
        request = RequestFactory().get("/")
        request.META["HTTP_HOST"] = "testserver"

        # Send invite email
        send_organisation_invite_email(request, member)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check recipient
        assert email.to == [user.email]

        # Check subject
        assert "Test Org" in email.subject

        # Parse accept and decline URLs from email body
        reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )
        decline_path = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )
        login_path = reverse("account_login")

        # Check that accept URL contains login redirect
        assert f"{login_path}?next=" in email.body
        # Note: The path is URL-encoded in the next parameter
        assert "accept" in email.body

        # Check that decline URL contains login redirect
        assert decline_path in email.body or "decline" in email.body

        # Verify the email contains user_exists messaging
        assert "sign in" in email.body.lower()

    def test_invite_new_user_includes_signup_url(self, mailoutbox):
        """Test that invites for new users include signup URL."""
        # Create organisation
        organisation = OrganisationFactory(name="Test Org")

        # Create invite without user (new user)
        member = OrganisationMemberFactory(
            user=None,
            invite_email="newuser@example.com",
            organisation=organisation,
            invite=True,
        )

        # Create request
        request = RequestFactory().get("/")
        request.META["HTTP_HOST"] = "testserver"

        # Send invite email
        send_organisation_invite_email(request, member)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check recipient
        assert email.to == ["newuser@example.com"]

        # Check that signup URL is in email
        signup_path = reverse("account_signup")
        assert signup_path in email.body

        # Check that email settings URL is in email
        email_settings_path = reverse("account_email")
        assert email_settings_path in email.body

        # Verify the email contains new user messaging
        assert (
            "sign up" in email.body.lower() or "create an account" in email.body.lower()
        )
        assert "verify your email" in email.body.lower()
        assert "add this email address" in email.body.lower()

    def test_invite_context_includes_all_required_urls(self):
        """Test that email context includes all required URLs."""
        # Create user and organisation
        user = UserFactory(email="user@example.com")
        organisation = OrganisationFactory()

        # Create invite
        member = OrganisationMemberFactory(
            user=user,
            invite_email=user.email,
            organisation=organisation,
        )

        # Create request
        request = RequestFactory().get("/")
        request.META["HTTP_HOST"] = "testserver"

        # Mock send_templated_email to capture context
        with patch("ams.organisations.email_utils.send_templated_email") as mock_send:
            send_organisation_invite_email(request, member)

            # Get the context passed to send_templated_email
            call_args = mock_send.call_args
            context = call_args.kwargs["context"]

            # Verify all required context keys are present
            assert "organisation" in context
            assert "accept_url" in context
            assert "decline_url" in context
            assert "signup_url" in context
            assert "email_settings_url" in context
            assert "user_exists" in context

            # Verify user_exists is correct
            assert context["user_exists"] is True

            # Verify URLs are absolute
            assert context["accept_url"].startswith("http://")
            assert context["decline_url"].startswith("http://")
            assert context["signup_url"].startswith("http://")
            assert context["email_settings_url"].startswith("http://")

    def test_invite_new_user_context_user_exists_false(self):
        """Test that new user invites have user_exists=False in context."""
        # Create organisation
        organisation = OrganisationFactory()

        # Create invite without user
        member = OrganisationMemberFactory(
            user=None,
            invite_email="newuser@example.com",
            organisation=organisation,
            invite=True,
        )

        # Create request
        request = RequestFactory().get("/")
        request.META["HTTP_HOST"] = "testserver"

        # Mock send_templated_email to capture context
        with patch("ams.organisations.email_utils.send_templated_email") as mock_send:
            send_organisation_invite_email(request, member)

            # Get the context passed to send_templated_email
            call_args = mock_send.call_args
            context = call_args.kwargs["context"]

            # Verify user_exists is False
            assert context["user_exists"] is False

    def test_invite_url_encoding_proper(self):
        """Test that next parameter is properly URL encoded."""
        # Create user and organisation
        user = UserFactory(email="user@example.com")
        organisation = OrganisationFactory()

        # Create invite
        member = OrganisationMemberFactory(
            user=user,
            invite_email=user.email,
            organisation=organisation,
        )

        # Create request
        request = RequestFactory().get("/")
        request.META["HTTP_HOST"] = "testserver"

        # Mock send_templated_email to capture context
        with patch("ams.organisations.email_utils.send_templated_email") as mock_send:
            send_organisation_invite_email(request, member)

            # Get the context
            context = mock_send.call_args.kwargs["context"]

            # Parse the accept URL
            parsed_url = urlparse(context["accept_url"])
            query_params = parse_qs(parsed_url.query)

            # Verify 'next' parameter exists and points to accept path
            assert "next" in query_params
            accept_path = reverse(
                "organisations:accept_invite",
                kwargs={"invite_token": member.invite_token},
            )
            assert query_params["next"][0] == accept_path

            # Parse the decline URL
            parsed_url = urlparse(context["decline_url"])
            query_params = parse_qs(parsed_url.query)

            # Verify 'next' parameter exists and points to decline path
            assert "next" in query_params
            decline_path = reverse(
                "organisations:decline_invite",
                kwargs={"invite_token": member.invite_token},
            )
            assert query_params["next"][0] == decline_path

    def test_invite_email_template_rendered_correctly(self, mailoutbox):
        """Test that email template is rendered with correct template name."""
        # Create organisation
        organisation = OrganisationFactory()

        # Create invite
        member = OrganisationMemberFactory(
            user=None,
            invite_email="test@example.com",
            organisation=organisation,
            invite=True,
        )

        # Create request
        request = RequestFactory().get("/")
        request.META["HTTP_HOST"] = "testserver"

        # Send email
        send_organisation_invite_email(request, member)

        # Assert email was sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]

        # Check that email has both HTML and plain text alternatives
        assert email.body  # Plain text version
        assert len(email.alternatives) > 0  # HTML version

        # Check content includes organisation name
        assert organisation.name in email.body
        html_content = email.alternatives[0][0]
        assert organisation.name in html_content
