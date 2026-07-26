"""Regression test for the Wagtail CMS user-creation form leaving
`username` blank, which broke the new user's first sign-in redirect
(`UserRedirectView` reverses `users:detail` on `request.user.username`).
"""

from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestWagtailUserCreationSetsUsername:
    def test_created_user_has_username_and_can_sign_in(self, client: Client):
        admin = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(admin)

        response = client.post(
            reverse("wagtailusers_users:add"),
            {
                "email": "newcmsuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "username": "newcmsuser",
                "password1": "a-very-strong-password-123",
                "password2": "a-very-strong-password-123",
                "groups": [],
            },
        )

        assert response.status_code == HTTPStatus.FOUND

        new_user = User.objects.get(email="newcmsuser@example.com")
        assert new_user.username == "newcmsuser"

        # Signing in immediately after creation must not hit a
        # NoReverseMatch on the `username`-based redirect.
        new_user_client = Client()
        new_user_client.force_login(new_user)
        redirect_response = new_user_client.get(reverse("users:redirect"))

        assert redirect_response.status_code == HTTPStatus.FOUND
        assert redirect_response.url == reverse(
            "users:detail",
            kwargs={"username": "newcmsuser"},
        )
