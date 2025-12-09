import time
import uuid
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import EmailField
from django.db.models import ForeignKey
from django.db.models import ImageField
from django.db.models import Model
from django.db.models import UUIDField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from config.storage_backends import PublicMediaStorage

from .managers import UserManager

# Custom username validator
username_validator = RegexValidator(
    regex=r"^[a-zA-ZāēīōūĀĒĪŌŪ0-9._-]+$",
    message=_(
        "Username must only include numbers, letters (including macrons), "
        "dashes, dots, and underscores.",
    ),
    code="invalid_username",
)

# --- User models ---


def user_profile_picture_path(instance, filename):
    """
    Generate upload path for user profile pictures.
    Uses user UUID and timestamp to ensure uniqueness and cache busting.
    Path format: profile-pictures/{user_uuid}/{timestamp}.{extension}
    """
    extension = filename.split(".")[-1] if "." in filename else "jpg"
    timestamp = int(time.time())
    return f"profile-pictures/{instance.uuid}/{timestamp}.{extension}"


class User(AbstractUser):
    """
    Default custom user model for Association Management Software.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    uuid = UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = EmailField(_("email address"), unique=True)
    username = CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "This is used in the community forum. Username must only include numbers, "
            "letters (including macrons), dashes, dots, and underscores.",
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = CharField(_("first name"), max_length=150, null=False, blank=False)
    last_name = CharField(_("last name"), max_length=150, null=False, blank=False)
    profile_picture = ImageField(
        _("profile picture"),
        upload_to=user_profile_picture_path,
        storage=PublicMediaStorage,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


# --- Organisation models ---


class OrganisationType(Model):
    name = CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


class OrganisationMember(Model):
    user = ForeignKey(
        User,
        null=True,
        on_delete=CASCADE,
        related_name="organisation_members",
    )
    invite_email = CharField(max_length=255, blank=True)
    invite_token = UUIDField(default=uuid.uuid4, editable=False)
    organisation = ForeignKey(
        Organisation,
        on_delete=CASCADE,
        related_name="organisation_members",
    )
    created_datetime = DateTimeField()
    accepted_datetime = DateTimeField(null=True)
    is_admin = BooleanField(default=False)

    class Meta:
        unique_together = (("user", "organisation"),)

    def __str__(self):
        if self.user:
            return self.user.get_full_name()
        return f"{self.invite_email} - {self.organisation.name} (Invite Pending)"

    def is_active(self) -> bool:
        """Returns true if the user has accepted the invite and verified their email."""
        active: bool = self.accepted_datetime and self.user and self.user.is_active
        return active
