import json
import re
import time
import uuid as uuid_lib
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.validators import RegexValidator
from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import EmailField
from django.db.models import ForeignKey
from django.db.models import ImageField
from django.db.models import Index
from django.db.models import IntegerField
from django.db.models import JSONField
from django.db.models import Model
from django.db.models import TextChoices
from django.db.models import TextField
from django.db.models import UUIDField
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
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
    admin_notes = TextField(
        _("admin notes"),
        blank=True,
        help_text=_("Internal notes for administrators only."),
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


# --- Profile Field models ---


class ProfileFieldGroup(Model):
    """
    Organizes profile fields into sections with multi-language headings/descriptions.
    """

    name_translations = JSONField(
        _("name translations"),
        default=dict,
        help_text=_('Enter translations as JSON: {"en": "Name", "mi": "Ingoa"}'),
    )
    description_translations = JSONField(
        _("description translations"),
        default=dict,
        blank=True,
        help_text=_(
            'Enter translations as JSON: {"en": "Description", "mi": "Whakamārama"}',
        ),
    )
    order = IntegerField(_("order"), default=0, help_text=_("Display order"))
    is_active = BooleanField(
        _("is active"),
        default=True,
        help_text=_("Show/hide group"),
    )

    class Meta:
        ordering = ["order"]
        verbose_name = _("profile field group")
        verbose_name_plural = _("profile field groups")

    def __str__(self):
        return self.get_name()

    def get_name(self, language_code=None):
        """Returns name for language (falls back to first available)."""
        if not language_code:
            language_code = get_language()

        if language_code and language_code in self.name_translations:
            return self.name_translations[language_code]

        # Fallback to first available translation
        if self.name_translations:
            return next(iter(self.name_translations.values()))

        return f"Group {self.pk}"

    def get_description(self, language_code=None):
        """Returns description for language (falls back to first available)."""
        if not language_code:
            language_code = get_language()

        if language_code and language_code in self.description_translations:
            return self.description_translations[language_code]

        # Fallback to first available translation
        if self.description_translations:
            return next(iter(self.description_translations.values()))

        return ""


class ProfileField(Model):
    """
    Defines individual profile questions with type, validation, and multi-language
    labels/help text.
    """

    class FieldType(TextChoices):
        TEXT = "TEXT", _("Text")
        TEXTAREA = "TEXTAREA", _("Textarea")
        CHECKBOX = "CHECKBOX", _("Checkbox")
        RADIO = "RADIO", _("Radio")
        DATE = "DATE", _("Date")
        MONTH = "MONTH", _("Month")
        NUMBER = "NUMBER", _("Number")
        SELECT = "SELECT", _("Select")

    field_key = CharField(
        _("field key"),
        max_length=100,
        unique=True,
        help_text=_("Unique identifier (lowercase_underscore format)"),
    )
    field_type = CharField(
        _("field type"),
        max_length=20,
        choices=FieldType.choices,
        help_text=_("Type of form field"),
    )
    label_translations = JSONField(
        _("label translations"),
        default=dict,
        help_text=_('Enter translations as JSON: {"en": "Label", "mi": "Tapanga"}'),
    )
    help_text_translations = JSONField(
        _("help text translations"),
        default=dict,
        blank=True,
        help_text=_('Enter translations as JSON: {"en": "Help text", "mi": "Āwhina"}'),
    )
    options = JSONField(
        _("options"),
        default=dict,
        blank=True,
        help_text=_(
            'For select/radio/checkbox: {"choices": [{"value": "val1", '
            '"label_translations": {"en": "Label 1", "mi": "..."}}]}',
        ),
    )
    min_value = IntegerField(
        _("min value"),
        null=True,
        blank=True,
        help_text=_("Minimum value for number fields"),
    )
    max_value = IntegerField(
        _("max value"),
        null=True,
        blank=True,
        help_text=_("Maximum value for number fields"),
    )
    is_read_only = BooleanField(
        _("is read only"),
        default=False,
        help_text=_("Only admins can set value"),
    )
    is_required_for_membership = BooleanField(
        _("is required for membership"),
        default=False,
        help_text=_("Required before membership purchase"),
    )
    counts_toward_completion = BooleanField(
        _("recommended to complete"),
        default=True,
        help_text=_("Include this field in profile completion percentage"),
    )
    order = IntegerField(
        _("order"),
        default=0,
        help_text=_("Display order within group"),
    )
    is_active = BooleanField(
        _("is active"),
        default=True,
        help_text=_("Show/hide field"),
    )
    group = ForeignKey(
        ProfileFieldGroup,
        on_delete=CASCADE,
        related_name="fields",
        verbose_name=_("group"),
    )

    class Meta:
        ordering = ["order"]
        unique_together = [["group", "field_key"]]
        verbose_name = _("profile field")
        verbose_name_plural = _("profile fields")

    def __str__(self):
        return self.get_label()

    def get_label(self, language_code=None):
        """Returns label for language (falls back to first available)."""
        if not language_code:
            language_code = get_language()

        if language_code and language_code in self.label_translations:
            return self.label_translations[language_code]

        # Fallback to first available translation
        if self.label_translations:
            return next(iter(self.label_translations.values()))

        return self.field_key

    def get_help_text(self, language_code=None):
        """Returns help text for language (falls back to first available)."""
        if not language_code:
            language_code = get_language()

        if language_code and language_code in self.help_text_translations:
            return self.help_text_translations[language_code]

        # Fallback to first available translation
        if self.help_text_translations:
            return next(iter(self.help_text_translations.values()))

        return ""

    def get_choices(self, language_code=None):
        """Returns list of tuples (value, translated_label) for
        select/radio/checkbox.
        """
        if not language_code:
            language_code = get_language()

        choices_list = self.options.get("choices", [])
        result = []

        for choice in choices_list:
            value = choice.get("value", "")
            label_translations = choice.get("label_translations", {})

            # Get translated label with fallback
            if language_code and language_code in label_translations:
                label = label_translations[language_code]
            elif label_translations:
                label = next(iter(label_translations.values()))
            else:
                label = value

            result.append((value, label))

        return result

    def clean(self):
        """Validate field configuration."""
        super().clean()
        if not re.match(r"^[a-z][a-z0-9_]*$", self.field_key):
            raise ValidationError(
                {
                    "field_key": _(
                        "Field key must start with a lowercase letter and contain only "
                        "lowercase letters, numbers, and underscores.",
                    ),
                },
            )

        # Validate label_translations is not empty
        if not self.label_translations:
            raise ValidationError(
                {"label_translations": _("Label translations cannot be empty.")},
            )

        # Validate options for select/radio/checkbox types
        if self.field_type in [
            self.FieldType.SELECT,
            self.FieldType.RADIO,
            self.FieldType.CHECKBOX,
        ]:
            if not self.options.get("choices"):
                raise ValidationError(
                    {
                        "options": _(
                            "Options must have a 'choices' list with "
                            "label_translations for select/radio/checkbox types.",
                        ),
                    },
                )

            # Validate each choice has label_translations
            for choice in self.options.get("choices", []):
                if not choice.get("label_translations"):
                    raise ValidationError(
                        {"options": _("Each choice must have label_translations.")},
                    )

        # Validate min_value < max_value for number fields
        if self.field_type == self.FieldType.NUMBER:
            if self.min_value is not None and self.max_value is not None:
                if self.min_value >= self.max_value:
                    raise ValidationError(
                        {
                            "min_value": _(
                                "Minimum value must be less than maximum value.",
                            ),
                        },
                    )


class ProfileFieldResponse(Model):
    """
    Stores individual user responses (EAV pattern: Entity=User, Attribute=ProfileField,
    Value=response).
    """

    user = ForeignKey(
        "User",
        on_delete=CASCADE,
        related_name="profile_responses",
        verbose_name=_("user"),
    )
    profile_field = ForeignKey(
        ProfileField,
        on_delete=CASCADE,
        related_name="responses",
        verbose_name=_("profile field"),
    )
    value = TextField(_("value"), blank=True, help_text=_("Response value"))
    updated_datetime = DateTimeField(
        _("updated datetime"),
        auto_now=True,
        help_text=_("When response was last updated"),
    )

    class Meta:
        unique_together = [["user", "profile_field"]]
        indexes = [
            Index(fields=["user"]),
            Index(fields=["profile_field"]),
        ]
        verbose_name = _("profile field response")
        verbose_name_plural = _("profile field responses")

    def __str__(self):
        return f"{self.user.email} - {self.profile_field.get_label()}"

    def get_value(self):
        """Returns parsed value (JSON decode for checkbox fields, proper type for
        others).
        """
        if not self.value:
            return None

        # For checkbox fields, parse JSON list
        if self.profile_field.field_type == ProfileField.FieldType.CHECKBOX:
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return []

        return self.value

    def set_value(self, value):
        """Stores value (JSON encode for lists, string for others)."""
        if value is None:
            self.value = ""
            return

        # For checkbox fields (lists), encode as JSON
        if isinstance(value, list):
            self.value = json.dumps(value)
        else:
            self.value = str(value)
