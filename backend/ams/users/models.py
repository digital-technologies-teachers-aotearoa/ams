from typing import Any, Tuple

from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    TextChoices,
)
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField


class MembershipOptionType(TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    ORGANISATION = "ORGANISATION", _("Organisation")


class MembershipOption(Model):
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=255, choices=MembershipOptionType.choices)
    duration = RelativeDeltaField()
    cost = DecimalField(max_digits=10, decimal_places=2)


class UserMembership(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="user_memberships")
    membership_option = ForeignKey(MembershipOption, on_delete=CASCADE, related_name="user_memberships")
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True)


class UserMemberStatus(TextChoices):
    NONE = "NONE", _("None")
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")


class UserMemberInfo:
    def __init__(self, user: User) -> None:
        self.user_membership = UserMembership.objects.filter(user=user).order_by("-created_datetime").first()

    def status(self) -> Tuple[str, Any]:
        if not self.user_membership:
            return UserMemberStatus.NONE

        if self.user_membership.approved_datetime is None:
            return UserMemberStatus.PENDING

        return UserMemberStatus.ACTIVE


def user_member_info(user: User) -> UserMemberInfo:
    if hasattr(user, "_member_info"):
        member_info: UserMemberInfo = user._member_info
        return member_info

    # Cache against user object
    user._member_info = UserMemberInfo(user)
    return user._member_info


User.member = property(lambda self: user_member_info(self))
