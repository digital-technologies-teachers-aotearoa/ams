from datetime import date
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import (
    CASCADE,
    SET_NULL,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    OneToOneField,
    TextChoices,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField


class UserProfile(Model):
    user = OneToOneField(User, on_delete=CASCADE, primary_key=True, related_name="profile")
    image = CharField(blank=True)


class OrganisationType(Model):
    name = CharField(max_length=255, unique=True)


class Organisation(Model):
    name = CharField(max_length=255)
    type = ForeignKey(OrganisationType, on_delete=CASCADE, related_name="organisations")
    telephone = CharField(max_length=255)
    email = CharField(max_length=255)
    contact_name = CharField(max_length=255)
    postal_address = CharField(max_length=255)
    postal_suburb = CharField(max_length=255, blank=True)
    postal_city = CharField(max_length=255)
    postal_code = CharField(max_length=255)
    street_address = CharField(max_length=255, blank=True)
    suburb = CharField(max_length=255, blank=True)
    city = CharField(max_length=255, blank=True)


class OrganisationMember(Model):
    user = ForeignKey(User, null=True, on_delete=CASCADE, related_name="organisation_members")
    invite_email = CharField(max_length=255, blank=True)
    invite_token = CharField(max_length=255, unique=True)
    organisation = ForeignKey(Organisation, on_delete=CASCADE, related_name="organisation_members")
    created_datetime = DateTimeField()
    accepted_datetime = DateTimeField(null=True)
    is_admin = BooleanField(default=False)

    def is_active(self) -> bool:
        # Check the user has accepted the invite and verified their email
        active: bool = self.accepted_datetime and self.user and self.user.is_active
        return active

    class Meta:
        unique_together = (("user", "organisation"),)


class MembershipOptionType(TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    ORGANISATION = "ORGANISATION", _("Organisation")


class MembershipOption(Model):
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=255, choices=MembershipOptionType.choices)
    duration = RelativeDeltaField()
    cost = DecimalField(max_digits=10, decimal_places=2)


class MembershipStatus(TextChoices):
    NONE = "NONE", _("None")
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    CANCELLED = "CANCELLED", _("Cancelled")


class OrganisationMembership(Model):
    organisation = ForeignKey(Organisation, on_delete=CASCADE, related_name="organisation_memberships")
    membership_option = ForeignKey(MembershipOption, on_delete=CASCADE, related_name="organisation_memberships")
    invoice = ForeignKey("billing.Invoice", on_delete=SET_NULL, null=True, related_name="organisation_memberships")
    start_date = DateField()
    created_datetime = DateTimeField()
    cancelled_datetime = DateTimeField(null=True)

    def expiry_date(self) -> date:
        # A membership is considered expired once the expiry date is reached
        # (it is not inclusive of the expiry date)
        expiry_date: date = self.start_date + self.membership_option.duration
        return expiry_date

    def is_expired(self) -> bool:
        is_expired: bool = timezone.localdate() >= self.expiry_date()
        return is_expired

    def expires_in_days(self) -> int:
        expires_in: int = (self.expiry_date() - timezone.localdate()).days
        return expires_in

    def status(self) -> Any:
        if self.cancelled_datetime:
            return MembershipStatus.CANCELLED

        if self.is_expired():
            return MembershipStatus.EXPIRED

        return MembershipStatus.ACTIVE


class UserMembership(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="user_memberships")
    membership_option = ForeignKey(MembershipOption, on_delete=CASCADE, related_name="user_memberships")
    invoice = ForeignKey("billing.Invoice", on_delete=SET_NULL, null=True, related_name="user_memberships")
    start_date = DateField()
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True)
    cancelled_datetime = DateTimeField(null=True)

    def expiry_date(self) -> date:
        # A membership is considered expired once the expiry date is reached
        # (it is not inclusive of the expiry date)
        expiry_date: date = self.start_date + self.membership_option.duration
        return expiry_date

    def is_expired(self) -> bool:
        is_expired: bool = timezone.localdate() >= self.expiry_date()
        return is_expired

    def expires_in_days(self) -> int:
        expires_in: int = (self.expiry_date() - timezone.localdate()).days
        return expires_in

    def status(self) -> Any:
        if self.cancelled_datetime:
            return MembershipStatus.CANCELLED

        if self.is_expired():
            return MembershipStatus.EXPIRED

        if self.approved_datetime is None or self.start_date > timezone.localdate():
            return MembershipStatus.PENDING

        return MembershipStatus.ACTIVE


class UserMemberInfo:
    def __init__(self, user: User) -> None:
        self.user = user
        self.current_user_membership: Optional[UserMembership] = user.get_current_user_membership()
        self.latest_user_membership: Optional[UserMembership] = user.get_latest_user_membership()
        self.has_active_organisation_membership: bool = self.check_has_organisation_with_active_membership()

    def check_has_organisation_with_active_membership(self) -> bool:
        if not self.user.is_active:
            return False

        # A user may belong to multiple organisations. If any have active memberships, return true
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM users_organisationmember AS org_member
                    JOIN users_organisationmembership AS org_membership
                      ON org_membership.organisation_id = org_member.organisation_id
                    JOIN users_membershipoption
                      ON users_membershipoption.id = org_membership.membership_option_id

                    -- user is an active member of organisation

                    WHERE org_member.user_id = %(user_id)s
                      AND org_member.accepted_datetime <= CURRENT_TIMESTAMP

                      -- the organisation has an active membership

                      AND (org_membership.start_date AT TIME ZONE %(time_zone)s)::timestamptz <= CURRENT_TIMESTAMP
                      AND (org_membership.start_date AT TIME ZONE %(time_zone)s)::timestamptz
                          + users_membershipoption.duration > CURRENT_TIMESTAMP
                      AND org_membership.cancelled_datetime IS NULL
                ) AS active
                """,
                {
                    "user_id": self.user.pk,
                    "time_zone": settings.TIME_ZONE,
                },
            )
            (active,) = cursor.fetchone()

        if active:
            return True
        return False

    def status(self) -> Any:
        if self.has_active_organisation_membership:
            return MembershipStatus.ACTIVE

        if self.current_user_membership:
            return self.current_user_membership.status()
        return MembershipStatus.NONE

    def latest_user_membership_is_cancelled(self) -> Optional[UserMembership]:
        # Only return if the membership with the maximum start datetime is cancelled and it is the only one
        latest_cancelled_user_membership: Optional[UserMembership] = (
            self.user.user_memberships.filter(cancelled_datetime__isnull=False).order_by("-start_date").first()
        )

        if latest_cancelled_user_membership and (
            not self.latest_user_membership
            or self.latest_user_membership.start_date < latest_cancelled_user_membership.start_date
        ):
            return latest_cancelled_user_membership

        return None


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


def get_current_user_membership(user: User) -> Optional[UserMembership]:
    current_user_membership: Optional[UserMembership] = (
        user.user_memberships.filter(cancelled_datetime__isnull=True, start_date__lte=timezone.localdate())
        .order_by("-start_date")
        .first()
    )
    return current_user_membership


def get_latest_user_membership(user: User) -> Optional[UserMembership]:
    latest_user_membership: Optional[UserMembership] = (
        user.user_memberships.filter(cancelled_datetime__isnull=True).order_by("-start_date").first()
    )
    return latest_user_membership


User.get_current_user_membership = get_current_user_membership
User.get_latest_user_membership = get_latest_user_membership

User.member = property(lambda self: user_member_info(self))
User.display_name = property(lambda self: get_display_name(self))
