from datetime import timedelta
from http import HTTPStatus
from io import BytesIO
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image

from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.users.forms import UserAdminChangeForm
from ams.users.forms import UserUpdateForm
from ams.users.models import Organisation
from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory
from ams.users.views import OrganisationCreateView
from ams.users.views import OrganisationUpdateView
from ams.users.views import UserRedirectView
from ams.users.views import UserUpdateView
from ams.users.views import user_detail_view

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def dummy_get_response(self, request: HttpRequest):
        return None

    def test_get_success_url(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request
        assert view.get_success_url() == f"/en/users/{user.username}/"

    def test_get_object(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user

    def test_form_valid(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = user

        view.request = request

        # Initialize the form
        form = UserAdminChangeForm()
        form.cleaned_data = {}
        form.instance = user
        view.form_valid(form)

        messages_sent = [m.message for m in messages.get_messages(request)]
        assert messages_sent == [_("Your user details have been successfully updated")]

    def test_update_view_with_profile_picture(self, user: User, client):
        """Test updating user with profile picture via POST request."""
        client.force_login(user)

        # Create a test image
        image = Image.new("RGB", (100, 100), color="green")
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        uploaded_file = SimpleUploadedFile(
            "new_profile.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        url = reverse("users:update")
        with patch("config.storage_backends.PublicMediaStorage.save") as mock_save:
            mock_save.return_value = f"profile_pictures/{user.uuid}/12345.jpg"

            response = client.post(
                url,
                {
                    "first_name": "Updated",
                    "last_name": "Name",
                    "username": user.username,
                    "profile_picture": uploaded_file,
                },
            )

        assert response.status_code == HTTPStatus.FOUND
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"

    def test_update_view_uses_correct_form(self, user: User, rf: RequestFactory):
        """Test that the update view uses UserUpdateForm."""
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user
        view.request = request

        assert view.form_class == UserUpdateForm


class TestUserRedirectView:
    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request
        assert view.get_redirect_url() == f"/en/users/{user.username}/"


class TestUserDetailView:
    def test_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = UserFactory()
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{login_url}?next=/fake-url/"


class TestOrganisationCreateView:
    """Tests for the OrganisationCreateView"""

    def test_create_organisation_authenticated(self, user: User, client):
        """Test that authenticated users can create organisations."""
        client.force_login(user)
        url = reverse("users:organisation_create")

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
        url = reverse("users:organisation_create")

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
        url = reverse("users:organisation_create")

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


class TestOrganisationUpdateView:
    """Tests for the OrganisationUpdateView"""

    def test_update_organisation_as_org_admin(self, user: User, client):
        """Test that organisation admins can update their organisation."""
        client.force_login(user)

        # Create organisation with user as admin
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        data = {
            "name": "Updated Organisation",
            "telephone": org.telephone,
            "email": org.email,
            "contact_name": org.contact_name,
            "postal_address": org.postal_address,
            "postal_city": org.postal_city,
            "postal_code": org.postal_code,
        }

        response = client.post(url, data=data)

        # Should redirect to home
        assert response.status_code == HTTPStatus.FOUND

        # Organisation should be updated
        org.refresh_from_db()
        assert org.name == "Updated Organisation"

    def test_update_organisation_as_staff(self, user: User, client):
        """Test that staff can update any organisation."""
        user.is_staff = True
        user.save()
        client.force_login(user)

        org = OrganisationFactory()

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        data = {
            "name": "Updated by Staff",
            "telephone": org.telephone,
            "email": org.email,
            "contact_name": org.contact_name,
            "postal_address": org.postal_address,
            "postal_city": org.postal_city,
            "postal_code": org.postal_code,
        }

        response = client.post(url, data=data)

        # Should redirect to home
        assert response.status_code == HTTPStatus.FOUND

        # Organisation should be updated
        org.refresh_from_db()
        assert org.name == "Updated by Staff"

    def test_update_organisation_no_permission(self, client):
        """Test that users without permission cannot update organisations."""
        user = UserFactory()
        client.force_login(user)

        org = OrganisationFactory()

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        data = {
            "name": "Unauthorized Update",
            "telephone": org.telephone,
            "email": org.email,
            "contact_name": org.contact_name,
            "postal_address": org.postal_address,
            "postal_city": org.postal_city,
            "postal_code": org.postal_code,
        }

        response = client.post(url, data=data)

        # Should return 403 Forbidden
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Organisation should NOT be updated
        org.refresh_from_db()
        assert org.name != "Unauthorized Update"

    def test_update_organisation_has_cancel_url(self, user: User, client):
        """Test that OrganisationUpdateView provides cancel_url to the form."""
        client.force_login(user)

        # Create organisation with user as admin
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

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

    def test_update_organisation_cancel_url_in_form_kwargs(self, user: User, rf):
        """Test that cancel_url is passed to form kwargs in OrganisationUpdateView."""
        # Create organisation with user as admin
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        request = rf.get("/fake-url/")
        request.user = user

        view = OrganisationUpdateView()
        view.request = request
        view.kwargs = {"uuid": org.uuid}

        form_kwargs = view.get_form_kwargs()

        expected_cancel_url = reverse(
            "users:organisation_detail",
            kwargs={"uuid": org.uuid},
        )
        assert "cancel_url" in form_kwargs
        assert form_kwargs["cancel_url"] == expected_cancel_url


@pytest.mark.django_db
class TestOrganisationDetailView:
    """Tests for OrganisationDetailView with focus on active membership detection."""

    def test_active_membership_current(self, user: User, client):
        """Test that a current active membership is correctly identified."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create an active membership (started 30 days ago, expires in 335 days)
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=30),
            expiry_date=timezone.now().date() + timedelta(days=335),
            cancelled_datetime=None,
            membership_option__type=MembershipOptionType.ORGANISATION,
            membership_option__max_seats=10,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership
        assert response.context["seat_limit"] == int(
            active_membership.membership_option.max_seats,
        )
        assert response.context["occupied_seats"] == active_membership.occupied_seats

    def test_expired_membership_not_active(self, user: User, client):
        """Test that an expired membership is not considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create an expired membership (expired yesterday)
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=365),
            expiry_date=timezone.now().date() - timedelta(days=1),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_future_membership_not_active(self, user: User, client):
        """Test that a future membership is not considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a future membership (starts tomorrow)
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() + timedelta(days=1),
            expiry_date=timezone.now().date() + timedelta(days=366),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_cancelled_membership_not_active(self, user: User, client):
        """Test that a cancelled membership is not considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a cancelled membership (would be active otherwise)
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=30),
            expiry_date=timezone.now().date() + timedelta(days=335),
            cancelled_datetime=timezone.now(),
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_multiple_memberships_only_active_shown(self, user: User, client):
        """Test that only the active membership is shown when multiple exist."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create past membership
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=730),
            expiry_date=timezone.now().date() - timedelta(days=365),
            cancelled_datetime=None,
        )

        # Create active membership
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=30),
            expiry_date=timezone.now().date() + timedelta(days=335),
            cancelled_datetime=None,
            membership_option__type=MembershipOptionType.ORGANISATION,
            membership_option__max_seats=10,
        )

        # Create future membership
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() + timedelta(days=335),
            expiry_date=timezone.now().date() + timedelta(days=700),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership
        assert response.context["seat_limit"] == int(
            active_membership.membership_option.max_seats,
        )
        assert response.context["occupied_seats"] == active_membership.occupied_seats

    def test_no_membership(self, user: User, client):
        """Test that organisations without memberships show no active membership."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_membership_starting_today(self, user: User, client):
        """Test that a membership starting today is considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a membership starting today
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership

    def test_membership_expiring_today(self, user: User, client):
        """Test that a membership expiring today is still considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a membership expiring today
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=365),
            expiry_date=timezone.now().date(),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership
