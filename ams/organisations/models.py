import uuid as uuid_lib

from django.db.models import CASCADE
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import Model
from django.db.models import Q
from django.db.models import TextChoices
from django.db.models import UniqueConstraint
from django.db.models import UUIDField
from django.utils.translation import gettext_lazy as _


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

    def __str__(self):
        return self.name


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
    role = CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text=_("Member role within the organisation"),
    )

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
