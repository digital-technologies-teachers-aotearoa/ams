"""Tests for user permission mixins."""

from http import HTTPStatus

import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.views.generic import DetailView

from ams.users.mixins import UserSelfOrStaffMixin
from ams.users.models import User
from ams.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserSelfOrStaffMixin:
    """Tests for UserSelfOrStaffMixin."""

    class _TestView(UserSelfOrStaffMixin, DetailView):
        """Test view using the mixin."""

        model = User
        template_name = "users/user_detail.html"

        def get_object(self, queryset=None):
            """Get user by username."""
            username = self.kwargs.get("username")
            return User.objects.get(username=username)

    def test_user_can_view_own_profile(self, rf: RequestFactory):
        """Test that users can view their own profile."""
        user = UserFactory()

        request = rf.get(f"/users/{user.username}/")
        request.user = user

        view = self._TestView.as_view()
        response = view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_staff_can_view_any_profile(self, rf: RequestFactory):
        """Test that staff can view any user's profile."""
        staff_user = UserFactory(is_staff=True)
        regular_user = UserFactory()

        request = rf.get(f"/users/{regular_user.username}/")
        request.user = staff_user

        view = self._TestView.as_view()
        response = view(request, username=regular_user.username)

        assert response.status_code == HTTPStatus.OK

    def test_superuser_can_view_any_profile(self, rf: RequestFactory):
        """Test that superusers can view any profile."""
        superuser = UserFactory(is_superuser=True)
        regular_user = UserFactory()

        request = rf.get(f"/users/{regular_user.username}/")
        request.user = superuser

        view = self._TestView.as_view()
        response = view(request, username=regular_user.username)

        assert response.status_code == HTTPStatus.OK

    def test_user_cannot_view_other_profile(self, rf: RequestFactory):
        """Test that regular users cannot view others' profiles."""
        user1 = UserFactory()
        user2 = UserFactory()

        request = rf.get(f"/users/{user2.username}/")
        request.user = user1

        view = self._TestView.as_view()

        with pytest.raises(PermissionDenied) as exc_info:
            view(request, username=user2.username)

        assert "You do not have permission to view this user profile" in str(
            exc_info.value,
        )

    def test_staff_user_can_view_own_profile(self, rf: RequestFactory):
        """Test that staff users can view their own profile."""
        staff_user = UserFactory(is_staff=True)

        request = rf.get(f"/users/{staff_user.username}/")
        request.user = staff_user

        view = self._TestView.as_view()
        response = view(request, username=staff_user.username)

        assert response.status_code == HTTPStatus.OK
