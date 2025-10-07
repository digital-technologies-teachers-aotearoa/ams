from django.urls import resolve
from django.urls import reverse

from ams.users.models import User


def test_detail(user: User):
    assert (
        reverse("users:detail", kwargs={"username": user.username})
        == f"/en/users/{user.username}/"
    )
    assert resolve(f"/en/users/{user.username}/").view_name == "users:detail"


def test_update():
    assert reverse("users:update") == "/en/users/~update/"
    assert resolve("/en/users/~update/").view_name == "users:update"


def test_redirect():
    assert reverse("users:redirect") == "/en/users/~redirect/"
    assert resolve("/en/users/~redirect/").view_name == "users:redirect"
