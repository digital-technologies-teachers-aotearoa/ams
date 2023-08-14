from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest


def user_is_admin(request: HttpRequest) -> bool:
    is_staff: bool = request.user.is_staff
    return is_staff


class UserIsAdminMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return user_is_admin(self.request)
