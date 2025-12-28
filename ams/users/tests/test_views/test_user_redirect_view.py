import pytest
from django.test import RequestFactory

from ams.users.models import User
from ams.users.views import UserRedirectView

pytestmark = pytest.mark.django_db


class TestUserRedirectView:
    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request
        assert view.get_redirect_url() == f"/en/users/{user.username}/"
