from datetime import date
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateField
from django.db.models import DateTimeField
from django.db.models import DecimalField
from django.db.models import ForeignKey
from django.db.models import Model
from django.db.models import QuerySet
from django.db.models import TextChoices
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField

from ams.memberships.duration import format_membership_duration
from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember

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
    invoice_reference = CharField(max_length=25, blank=True)
    max_seats = DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=_(
            "Maximum number of seats for organisation memberships (optional limit)",
        ),
    )
    archived = BooleanField(
        default=False,
        help_text=_("Mark as archived to prevent new signups"),
    )

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

    def delete(self, *args, **kwargs):
        """Prevent deletion if there are related memberships."""
        if (
            self.individual_memberships.exists()
            or self.organisation_memberships.exists()
        ):
            raise ValidationError(
                _(
                    "Cannot delete membership option with existing memberships. "
                    "Archive it instead.",
                ),
            )
        return super().delete(*args, **kwargs)


class BaseMembership(Model):
    """Abstract base class for membership models."""

    start_date = DateField()
    expiry_date = DateField()
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True, blank=True)
    cancelled_datetime = DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def clean(self):
        # Enforce expiry_date is after start_date
        if self.expiry_date and self.start_date and self.expiry_date <= self.start_date:
            raise ValidationError(
                {"expiry_date": "Expiry date must be after start date."},
            )
        super().clean()

    def calculate_expiry_date(self) -> date:
        # Calculate expiry date based on start_date and membership_option.duration
        return self.start_date + self.membership_option.duration

    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return timezone.localdate() >= self.expiry_date

    def status(self) -> Any:
        if self.cancelled_datetime:
            return MembershipStatus.CANCELLED

        if self.is_expired():
            return MembershipStatus.EXPIRED

        if self.approved_datetime is None or self.start_date > timezone.localdate():
            return MembershipStatus.PENDING

        return MembershipStatus.ACTIVE

    def get_status_display(self) -> str:
        # Always use MembershipStatus display name
        try:
            return MembershipStatus(self.status()).label
        except ValueError:
            return str(self.status())


class IndividualMembershipQuerySet(QuerySet):
    """Custom queryset for IndividualMembership model."""

    def active(self):
        """Return only active memberships."""
        today = timezone.localdate()
        return self.filter(
            approved_datetime__isnull=False,
            cancelled_datetime__isnull=True,
            start_date__lte=today,
            expiry_date__gt=today,
        )


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

    objects = IndividualMembershipQuerySet.as_manager()

    class Meta:
        verbose_name = "Membership: Individual"
        verbose_name_plural = "Membership: Individual"

    def __str__(self):
        return (
            f"{self.user.get_full_name()} - {self.membership_option.name} - "
            f"Status: {self.status()}"
        )


class OrganisationMembershipQuerySet(QuerySet):
    def active(self):
        today = timezone.localdate()
        return self.filter(
            approved_datetime__isnull=False,
            cancelled_datetime__isnull=True,
            start_date__lte=today,
            expiry_date__gt=today,
        )


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
    seats = DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text=_(
            "Number of seats allocated to this membership. "
            "Cannot exceed the membership option's max_seats limit if set.",
        ),
    )

    objects = OrganisationMembershipQuerySet.as_manager()

    class Meta:
        verbose_name = "Membership: Organisation"
        verbose_name_plural = "Membership: Organisation"

    def __str__(self):
        return (
            f"{self.organisation.name} - {self.membership_option.name} - "
            f"Status: {self.status()}"
        )

    @property
    def occupied_seats(self) -> int:
        """Calculate the number of seats currently occupied by active members.

        Only counts seats if this membership is currently active.
        """
        # Only count occupied seats if this membership is active or pending
        current_status = self.status()
        if current_status not in (MembershipStatus.ACTIVE, MembershipStatus.PENDING):
            return 0

        return OrganisationMember.objects.filter(
            organisation=self.organisation,
            accepted_datetime__isnull=False,
            user__is_active=True,
        ).count()

    @property
    def has_seat_limit(self) -> bool:
        """Check if this membership has a seat limit configured."""
        return bool(self.membership_option.max_seats)

    @property
    def seats_available(self) -> int | None:
        """
        Calculate number of available seats.

        Returns:
            int: Number of available seats (0 if full)
        """
        return max(0, int(self.seats) - self.occupied_seats)

    @property
    def is_full(self) -> bool:
        """Check if all membership seats are occupied."""
        return self.occupied_seats >= int(self.seats)

    def seats_summary(self) -> str:
        """Return summary of seat status."""
        base = f"Occupied: {self.occupied_seats} / {self.seats}"
        if self.membership_option.max_seats:
            max_seats = self.membership_option.max_seats
            if max_seats == 1:
                limit = f"Membership has limit of {max_seats} seat"
            else:
                limit = f"Membership has limit of {max_seats} seats"
            return f"{base} ({limit})"
        return base
