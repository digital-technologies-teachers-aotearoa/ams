import uuid as uuid_lib

from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import Model
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import TextChoices
from django.db.models import UniqueConstraint
from django.db.models import UUIDField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class OrganisationMemberQuerySet(QuerySet):
    """Custom queryset for OrganisationMember model."""

    def active(self):
        """Return only active members (not declined or revoked)."""
        return self.filter(
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        )

    def admins(self):
        """Return only admin members."""
        return self.filter(role="ADMIN")

    def active_admins(self):
        """Return only active admin members."""
        return self.active().admins()

    def for_organisation(self, organisation):
        """Filter members by organisation."""
        return self.filter(organisation=organisation)


class OrganisationQuerySet(QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Organisation(Model):
    uuid = UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
    name = CharField(max_length=255)
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
    is_active = BooleanField(
        default=True,
        help_text=_(
            "Designates whether this organisation should be treated as active. "
            "Unselect this instead of deleting organisations.",
        ),
        verbose_name=_("active"),
    )

    objects = OrganisationQuerySet.as_manager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Detect is_active change from True → False
        if self.pk:
            try:
                old = Organisation.objects.get(pk=self.pk)
                if old.is_active and not self.is_active:
                    # Save first to ensure is_active is updated
                    super().save(*args, **kwargs)

                    # Auto-cancel memberships
                    self.organisation_memberships.filter(
                        cancelled_datetime__isnull=True,
                    ).update(cancelled_datetime=timezone.now())

                    # Auto-revoke pending invites
                    self.organisation_members.filter(
                        accepted_datetime__isnull=True,
                        declined_datetime__isnull=True,
                        revoked_datetime__isnull=True,
                    ).update(revoked_datetime=timezone.now())
                    return
            except Organisation.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def get_active_membership(self):
        """Get the active membership with related option, or None."""
        return (
            self.organisation_memberships.active()
            .select_related("membership_option")
            .first()
        )

    def has_minimum_admin_count(self, minimum=1):
        """Check if org has at least minimum number of active admins."""
        return self.organisation_members.active_admins().count() >= minimum

    @property
    def has_active_membership(self) -> bool:
        """Check if organisation has an active membership."""
        return self.organisation_memberships.active().exists()


class OrganisationMember(Model):
    class Role(TextChoices):
        ADMIN = "ADMIN", _("Admin")
        MEMBER = "MEMBER", _("Member")

    uuid = UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
    user = ForeignKey(
        "users.User",
        null=True,
        on_delete=CASCADE,
        related_name="organisation_members",
    )
    invite_email = CharField(max_length=255, blank=True)
    invite_token = UUIDField(default=uuid_lib.uuid4, editable=False)
    organisation = ForeignKey(
        Organisation,
        on_delete=CASCADE,
        related_name="organisation_members",
    )
    created_datetime = DateTimeField()
    accepted_datetime = DateTimeField(null=True)
    declined_datetime = DateTimeField(null=True)
    revoked_datetime = DateTimeField(null=True)
    last_sent_datetime = DateTimeField(
        null=True,
        help_text=_("Timestamp of when invite was last sent/resent"),
    )
    role = CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text=_("Member role within the organisation"),
    )

    objects = OrganisationMemberQuerySet.as_manager()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "organisation"],
                condition=Q(
                    declined_datetime__isnull=True,
                    revoked_datetime__isnull=True,
                ),
                name="unique_active_org_member",
            ),
        ]

    def __str__(self):
        if self.user:
            return self.user.get_full_name()
        return f"{self.invite_email} - {self.organisation.name} (Invite Pending)"

    def is_active(self) -> bool:
        """Returns true if the user has accepted the invite and verified their email."""
        return bool(self.accepted_datetime and self.user and self.user.is_active)
