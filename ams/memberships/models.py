from datetime import date
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.db.models import CharField
from django.db.models import DateField
from django.db.models import DateTimeField
from django.db.models import DecimalField
from django.db.models import ForeignKey
from django.db.models import Model
from django.db.models import TextChoices
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField

from ams.memberships.duration import format_membership_duration
from ams.users.models import Organisation

User = get_user_model()


# --- Membership generic models ---


class MembershipOptionType(TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    ORGANISATION = "ORGANISATION", _("Organisation")


class MembershipStatus(TextChoices):
    NONE = "NONE", _("None")
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    CANCELLED = "CANCELLED", _("Cancelled")


class MembershipOption(Model):
    name = CharField(max_length=255)
    type = CharField(max_length=255, choices=MembershipOptionType)
    duration = RelativeDeltaField()
    cost = DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = (("name", "type"),)

    def __str__(self):
        return (
            f"{self.name} ({self.get_type_display()}) - "
            f"Duration: {self.duration_display} - Cost: ${self.cost}"
        )

    @property
    def duration_display(self):
        return format_membership_duration(self.duration)


class IndividualMembership(Model):
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name="individual_memberships",
    )
    membership_option = ForeignKey(
        MembershipOption,
        on_delete=CASCADE,
        related_name="individual_memberships",
    )
    invoice = ForeignKey(
        "billing.Invoice",
        on_delete=SET_NULL,
        null=True,
        related_name="individual_memberships",
    )
    start_date = DateField()
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True)
    cancelled_datetime = DateTimeField(null=True)

    def __str__(self):
        return (
            f"{self.user.get_full_name()} - {self.membership_option.name} - "
            f"Status: {self.status()}"
        )

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


class OrganisationMembership(Model):
    organisation = ForeignKey(
        Organisation,
        on_delete=CASCADE,
        related_name="organisation_memberships",
    )
    membership_option = ForeignKey(
        MembershipOption,
        on_delete=CASCADE,
        related_name="organisation_memberships",
    )
    invoice = ForeignKey(
        "billing.Invoice",
        on_delete=SET_NULL,
        null=True,
        related_name="organisation_memberships",
    )
    start_date = DateField()
    created_datetime = DateTimeField()
    cancelled_datetime = DateTimeField(null=True)

    def __str__(self):
        return (
            f"{self.organisation.name} - {self.membership_option.name} - "
            f"Status: {self.status()}"
        )

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
