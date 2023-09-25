from datetime import date
from typing import Any, Optional

from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    TextChoices,
    TextField,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField


class OrganisationType(Model):
    name = CharField(max_length=255, unique=True)


class Organisation(Model):
    name = CharField(max_length=255)
    type = ForeignKey(OrganisationType, on_delete=CASCADE, related_name="organisations")
    postal_address = TextField(blank=True)
    office_phone = CharField(max_length=255, blank=True)


class MembershipOptionType(TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    ORGANISATION = "ORGANISATION", _("Organisation")


class MembershipOption(Model):
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=255, choices=MembershipOptionType.choices)
    duration = RelativeDeltaField()
    cost = DecimalField(max_digits=10, decimal_places=2)


class UserMemberStatus(TextChoices):
    NONE = "NONE", _("None")
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")


class UserMembership(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="user_memberships")
    membership_option = ForeignKey(MembershipOption, on_delete=CASCADE, related_name="user_memberships")
    start_date = DateField()
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True)

    def expiry_date(self) -> date:
        # A membership is considered expired once the expiry date is reached
        # (it is not inclusive of the expiry date)
        expiry_date: date = self.start_date + self.membership_option.duration
        return expiry_date

    def expires_in_days(self) -> int:
        expires_in: int = (self.expiry_date() - timezone.localdate()).days
        return expires_in

    def status(self) -> Any:
        if timezone.localdate() >= self.expiry_date():
            return UserMemberStatus.EXPIRED

        if self.approved_datetime is None or self.start_date > timezone.localdate():
            return UserMemberStatus.PENDING

        return UserMemberStatus.ACTIVE


class UserMemberInfo:
    def __init__(self, user: User) -> None:
        self.current_membership: Optional[UserMembership] = user.get_current_membership()
        self.latest_membership: Optional[UserMembership] = user.get_latest_membership()


def user_member_info(user: User) -> UserMemberInfo:
    if hasattr(user, "_member_info"):
        member_info: UserMemberInfo = user._member_info
        return member_info

    # Cache against user object
    user._member_info = UserMemberInfo(user)
    return user._member_info


def get_display_name(user: User) -> str:
    display_name: str = user.get_full_name()
    return display_name


def get_current_membership(user: User) -> Optional[UserMembership]:
    current_membership: Optional[UserMembership] = (
        user.user_memberships.filter(start_date__lte=timezone.localdate()).order_by("-start_date").first()
    )
    return current_membership


def get_latest_membership(user: User) -> Optional[UserMembership]:
    latest_membership: Optional[UserMembership] = user.user_memberships.order_by("-start_date").first()
    return latest_membership


User.get_current_membership = get_current_membership
User.get_latest_membership = get_latest_membership

User.member = property(lambda self: user_member_info(self))
User.display_name = property(lambda self: get_display_name(self))
