from datetime import date
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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


class BaseMembership(Model):
    """Abstract base class for membership models."""

    start_date = DateField()
    expiry_date = DateField()
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True)
    cancelled_datetime = DateTimeField(null=True)

    class Meta:
        abstract = True

    def clean(self):
        # Enforce expiry_date is after start_date
        if self.expiry_date and self.start_date and self.expiry_date <= self.start_date:
            raise ValidationError(
                {"expiry_date": "Expiry date must be after start date."},
            )
        super().clean()

    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return timezone.localdate() >= self.expiry_date

    def get_status_display(self) -> str:
        # Always use MembershipStatus display name
        try:
            return MembershipStatus(self.status()).label
        except ValueError:
            return str(self.status())


class IndividualMembership(BaseMembership):
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
        blank=True,
        related_name="individual_memberships",
    )

    class Meta:
        verbose_name = "Membership: Individual"
        verbose_name_plural = "Membership: Individual"

    def __str__(self):
        return (
            f"{self.user.get_full_name()} - {self.membership_option.name} - "
            f"Status: {self.status()}"
        )

    def status(self) -> Any:
        if self.cancelled_datetime:
            return MembershipStatus.CANCELLED

        if self.is_expired():
            return MembershipStatus.EXPIRED

        if self.approved_datetime is None or self.start_date > timezone.localdate():
            return MembershipStatus.PENDING

        return MembershipStatus.ACTIVE


class OrganisationMembership(BaseMembership):
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
        blank=True,
        related_name="organisation_memberships",
    )

    class Meta:
        verbose_name = "Membership: Organisation"
        verbose_name_plural = "Membership: Organisation"

    def __str__(self):
        return (
            f"{self.organisation.name} - {self.membership_option.name} - "
            f"Status: {self.status()}"
        )

    def calculate_expiry_date(self) -> date:
        # Calculate expiry date based on start_date and membership_option.duration
        return self.start_date + self.membership_option.duration

    def status(self) -> Any:
        if self.cancelled_datetime:
            return MembershipStatus.CANCELLED

        if self.is_expired():
            return MembershipStatus.EXPIRED

        return MembershipStatus.ACTIVE
