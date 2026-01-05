from http import HTTPStatus

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember
from ams.organisations.views import OrganisationCreateView
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOrganisationCreateView:
    """Tests for the OrganisationCreateView"""

    def test_create_organisation_authenticated(self, user: User, client):
        """Test that authenticated users can create organisations."""
        client.force_login(user)
        url = reverse("organisations:create")

        data = {
            "name": "New Organisation",
            "telephone": "021234567",
            "email": "org@example.com",
            "contact_name": "John Doe",
            "postal_address": "123 Test St",
            "postal_city": "City",
            "postal_code": "1234",
        }

        response = client.post(url, data=data)

        # Should redirect to home
        assert response.status_code == HTTPStatus.FOUND

        # Organisation should be created
        org = Organisation.objects.get(name="New Organisation")
        assert org.email == "org@example.com"

        # User should be added as an admin
        member = OrganisationMember.objects.get(
            organisation=org,
            user=user,
        )
        assert member.role == OrganisationMember.Role.ADMIN
        assert member.accepted_datetime is not None

    def test_create_organisation_not_authenticated(self, client):
        """Test that unauthenticated users cannot create organisations."""
        url = reverse("organisations:create")

        data = {
            "name": "New Organisation",
            "telephone": "021234567",
            "email": "org@example.com",
            "contact_name": "John Doe",
            "postal_address": "123 Test St",
            "postal_city": "City",
            "postal_code": "1234",
        }

        response = client.post(url, data=data)

        # Should redirect to login
        login_url = reverse(settings.LOGIN_URL)
        assert response.status_code == HTTPStatus.FOUND
        assert login_url in response.url

    def test_create_organisation_has_cancel_url(self, user: User, client):
        """Test that OrganisationCreateView provides cancel_url to the form."""
        client.force_login(user)
        url = reverse("organisations:create")

        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        # Check that the cancel link is present in the rendered form
        expected_cancel_url = reverse(
            "users:detail",
            kwargs={"username": user.username},
        )
        assert expected_cancel_url in response.content.decode()
        # Check for the Cancel button
        assert "Cancel" in response.content.decode()

    def test_create_organisation_cancel_url_in_form_kwargs(self, user: User, rf):
        """Test that cancel_url is passed to form kwargs in OrganisationCreateView."""

        request = rf.get("/fake-url/")
        request.user = user

        view = OrganisationCreateView()
        view.request = request

        form_kwargs = view.get_form_kwargs()

        expected_cancel_url = reverse(
            "users:detail",
            kwargs={"username": user.username},
        )
        assert "cancel_url" in form_kwargs
        assert form_kwargs["cancel_url"] == expected_cancel_url

    def test_create_organisation_sends_staff_notification(
        self,
        user: User,
        client,
        mailoutbox,
    ):
        """Test that creating an organisation sends notification to staff."""
        # Create staff users
        staff1 = UserFactory(is_staff=True, email="staff1@example.com")
        staff2 = UserFactory(is_staff=True, email="staff2@example.com")

        client.force_login(user)
        url = reverse("organisations:create")

        data = {
            "name": "New Organisation",
            "telephone": "021234567",
            "email": "org@example.com",
            "contact_name": "John Doe",
            "postal_address": "123 Test St",
            "postal_city": "City",
            "postal_code": "1234",
        }

        response = client.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND

        # Staff notification should be sent
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert "New Organisation" in email.subject
        assert set(email.to) == {staff1.email, staff2.email}
        assert "New Organisation" in email.body

    @override_settings(NOTIFY_STAFF_ORGANISATION_EVENTS=False)
    def test_create_organisation_no_notification_when_disabled(
        self,
        user: User,
        client,
        mailoutbox,
    ):
        """Test that notification is not sent when feature is disabled."""
        UserFactory(is_staff=True, email="staff@example.com")

        client.force_login(user)
        url = reverse("organisations:create")

        data = {
            "name": "New Organisation",
            "telephone": "021234567",
            "email": "org@example.com",
            "contact_name": "John Doe",
            "postal_address": "123 Test St",
            "postal_city": "City",
            "postal_code": "1234",
        }

        response = client.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND
        assert len(mailoutbox) == 0  # No notification sent
