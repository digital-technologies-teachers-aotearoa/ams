from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse

from ams.users.models import User
from ams.users.tests.factories import UserFactory
from ams.users.views import user_detail_view

pytestmark = pytest.mark.django_db


class TestUserDetailView:
    def test_user_can_view_own_profile(self, user: User, rf: RequestFactory):
        """Test authenticated user can view their own profile."""
        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_user_cannot_view_other_profile(self, user: User, rf: RequestFactory):
        """Test user cannot view another user's profile."""
        other_user = UserFactory()
        request = rf.get("/fake-url/")
        request.user = other_user

        with pytest.raises(PermissionDenied):
            user_detail_view(request, username=user.username)

    def test_staff_can_view_any_profile(self, user: User, rf: RequestFactory):
        """Test staff can view any user's profile."""
        staff_user = UserFactory(is_staff=True)
        request = rf.get("/fake-url/")
        request.user = staff_user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_superuser_can_view_any_profile(self, user: User, rf: RequestFactory):
        """Test superuser can view any user's profile."""
        superuser = UserFactory(is_superuser=True)
        request = rf.get("/fake-url/")
        request.user = superuser
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        """Test unauthenticated users are redirected to login."""
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{login_url}?next=/fake-url/"
