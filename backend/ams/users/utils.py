from typing import Any, Dict

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.request import HttpRequest


def user_is_admin(request: HttpRequest) -> bool:
    is_staff: bool = request.user.is_staff
    return is_staff


def user_message(message: Any, message_type: str = "success") -> Dict[str, Any]:
    return {"value": message, "type": message_type}


class UserIsAdminMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return user_is_admin(self.request)
