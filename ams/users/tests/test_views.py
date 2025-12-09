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
from django.utils.translation import gettext_lazy as _
from PIL import Image

from ams.users.forms import UserAdminChangeForm
from ams.users.forms import UserUpdateForm
from ams.users.models import User
from ams.users.tests.factories import UserFactory
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
