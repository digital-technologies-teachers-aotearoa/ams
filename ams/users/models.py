import time
import uuid as uuid_lib
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.files.storage import storages
from django.core.validators import RegexValidator
from django.db.models import CharField
from django.db.models import EmailField
from django.db.models import ImageField
from django.db.models import UUIDField
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from .managers import UserManager

# Custom username validator
USERNAME_REGEX = r"^[a-zA-ZāēīōūĀĒĪŌŪ0-9._-]+$"

username_validator = RegexValidator(
    regex=USERNAME_REGEX,
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
    Path format: profile_pictures/{user_uuid}/{timestamp}.{extension}
    """
    extension = filename.split(".")[-1] if "." in filename else "jpg"
    timestamp = int(time.time())
    return f"profile_pictures/{instance.uuid}/{timestamp}.{extension}"


def get_public_media_storage():
    """Get the configured public media storage backend."""
    return storages["default"]


class User(AbstractUser):
    """
    Default custom user model for Association Management Software.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    uuid = UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
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
        storage=get_public_media_storage,
        blank=True,
    )
    profile_picture_thumbnail = ImageSpecField(
        source="profile_picture",
        processors=[ResizeToFill(800, 800)],
        format="JPEG",
        options={"quality": 80},
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

    def has_active_individual_membership(self) -> bool:
        """Check if user has an active individual membership."""
        return self.individual_memberships.active().exists()

    def has_active_organisation_membership(self) -> bool:
        """Check if user is member of org with active membership."""
        return self.organisation_members.filter(
            accepted_datetime__isnull=False,
            declined_datetime__isnull=True,
            user__is_active=True,
            organisation__is_active=True,
            organisation__organisation_memberships__cancelled_datetime__isnull=True,
            organisation__organisation_memberships__start_date__lte=timezone.localdate(),
            organisation__organisation_memberships__expiry_date__gt=timezone.localdate(),
        ).exists()

    def check_has_active_membership_core(self) -> bool:
        """
        Core logic to check if user has an active membership.

        Checks for:
        - Active individual membership OR
        - Active membership in any organization the user belongs to

        Returns:
            bool: True if user has active membership, False otherwise
        """
        return (
            self.has_active_individual_membership()
            or self.has_active_organisation_membership()
        )
