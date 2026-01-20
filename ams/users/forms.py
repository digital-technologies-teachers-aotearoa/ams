from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django.contrib.auth import forms as admin_forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import ChoiceField
from django.forms import DateField
from django.forms import DateInput
from django.forms import EmailField
from django.forms import ImageField
from django.forms import IntegerField
from django.forms import ModelForm
from django.forms import MultipleChoiceField
from django.forms import NumberInput
from django.forms import RadioSelect
from django.forms import Select
from django.forms import Textarea
from django.forms import TextInput
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from ams.users.models import ProfileField
from ams.users.models import ProfileFieldResponse
from ams.users.models import User
from ams.utils.crispy_forms import Cancel
from ams.utils.crispy_forms import ProfileFieldWithBadges


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email", "first_name", "last_name", "username")
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """

    first_name = CharField(
        label="First name",
        max_length=150,
        widget=TextInput(
            attrs={"placeholder": _("First name"), "autocomplete": "first_name"},
        ),
    )
    last_name = CharField(
        label="Last name",
        max_length=150,
        widget=TextInput(
            attrs={"placeholder": _("Last name"), "autocomplete": "last_name"},
        ),
    )
    username = CharField(
        label="Username",
        max_length=150,
        help_text="This is used in the community forum.",
        widget=TextInput(
            attrs={"placeholder": _("Username"), "autocomplete": "username"},
        ),
    )

    field_order = [
        "email",
        "password1",
        "password2",
        "first_name",
        "last_name",
        "username",
    ]

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.username = self.cleaned_data.get("username")
        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class UserUpdateForm(ModelForm):
    """
    Form for updating user profile information including profile picture and dynamic
    profile fields.
    """

    profile_picture = ImageField(
        label=_("Profile picture"),
        required=False,
        help_text=_(
            "Upload a profile picture (JPEG, PNG, GIF, or WEBP). "
            "Maximum file size: 5MB.",
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "profile_picture"]
        widgets = {
            "first_name": TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": TextInput(attrs={"autocomplete": "family-name"}),
            "username": TextInput(attrs={"autocomplete": "username"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form and add dynamic profile fields."""
        super().__init__(*args, **kwargs)

        language_code = get_language()
        self._profile_fields = []

        existing_responses = self._load_existing_responses()
        profile_fields = self._add_profile_fields_to_form(
            language_code,
            existing_responses,
        )

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "d-flex flex-column gap-4 mt-4"
        self._build_crispy_layout(profile_fields, language_code)

    def _load_existing_responses(self):
        """Load existing profile field responses for the user."""
        if not (self.instance and self.instance.pk):
            return {}
        responses = ProfileFieldResponse.objects.filter(
            user=self.instance,
        ).select_related("profile_field", "profile_field__group")
        return {resp.profile_field.field_key: resp.get_value() for resp in responses}

    def _get_active_profile_fields(self):
        """Query and return active profile fields."""
        return (
            ProfileField.objects.filter(is_active=True)
            .select_related("group")
            .order_by("group__order", "order")
        )

    def _group_fields_by_group(self, profile_fields, language_code):
        """Organize profile fields by ProfileFieldGroup."""
        fields_by_group = {}
        for profile_field in profile_fields:
            group_name = profile_field.group.get_name(language_code)
            if group_name not in fields_by_group:
                fields_by_group[group_name] = {
                    "group": profile_field.group,
                    "fields": [],
                }
            fields_by_group[group_name]["fields"].append(profile_field)
        return fields_by_group

    def _create_form_field_for_profile_field(  # noqa: PLR0911
        self,
        profile_field,
        language_code,
        initial,
    ):
        """Create a Django form field for a ProfileField based on its type."""
        field_type = profile_field.field_type
        label = profile_field.get_label(language_code)
        help_text = profile_field.get_help_text(language_code)

        if field_type == ProfileField.FieldType.TEXT:
            return CharField(
                label=label,
                help_text=help_text,
                required=False,
                widget=TextInput(),
                initial=initial,
            )
        if field_type == ProfileField.FieldType.TEXTAREA:
            return CharField(
                label=label,
                help_text=help_text,
                required=False,
                widget=Textarea(attrs={"rows": 4}),
                initial=initial,
            )
        if field_type == ProfileField.FieldType.CHECKBOX:
            choices = profile_field.get_choices(language_code)
            return MultipleChoiceField(
                label=label,
                help_text=help_text,
                required=False,
                choices=choices,
                widget=CheckboxSelectMultiple(),
                initial=initial if isinstance(initial, list) else [],
            )
        if field_type == ProfileField.FieldType.RADIO:
            choices = profile_field.get_choices(language_code)
            return ChoiceField(
                label=label,
                help_text=help_text,
                required=False,
                choices=choices,
                widget=RadioSelect(),
                initial=initial,
            )
        if field_type == ProfileField.FieldType.DATE:
            return DateField(
                label=label,
                help_text=help_text,
                required=False,
                widget=DateInput(attrs={"type": "date"}),
                initial=initial,
            )
        if field_type == ProfileField.FieldType.MONTH:
            return CharField(
                label=label,
                help_text=help_text,
                required=False,
                widget=TextInput(attrs={"type": "month"}),
                initial=initial,
            )
        if field_type == ProfileField.FieldType.NUMBER:
            return IntegerField(
                label=label,
                help_text=help_text,
                required=False,
                widget=NumberInput(),
                min_value=profile_field.min_value,
                max_value=profile_field.max_value,
                initial=initial,
            )
        if field_type == ProfileField.FieldType.SELECT:
            choices = profile_field.get_choices(language_code)
            return ChoiceField(
                label=label,
                help_text=help_text,
                required=False,
                choices=[("", ""), *choices],
                widget=Select(),
                initial=initial,
            )
        return None

    def _apply_field_permissions(self, profile_field, form_field):
        """Apply read-only restrictions to form field if needed."""
        if profile_field.is_read_only:
            user = self.instance
            if not (user and user.is_staff):
                form_field.widget.attrs["disabled"] = True

    def _add_profile_fields_to_form(self, language_code, existing_responses):
        """Add all dynamic profile fields to the form."""
        profile_fields = self._get_active_profile_fields()

        for profile_field in profile_fields:
            field_key = profile_field.field_key
            initial = existing_responses.get(field_key)

            form_field = self._create_form_field_for_profile_field(
                profile_field,
                language_code,
                initial,
            )

            if form_field:
                self._apply_field_permissions(profile_field, form_field)
                self.fields[field_key] = form_field
                self._profile_fields.append(profile_field)

        return profile_fields

    def _build_crispy_layout(self, profile_fields, language_code):
        """Build the crispy forms layout with fieldsets."""
        fields_by_group = self._group_fields_by_group(profile_fields, language_code)

        layout_elements = [
            Fieldset(
                _("Personal Information"),
                "first_name",
                "last_name",
                "username",
                "profile_picture",
            ),
        ]

        for group_name, group_data in fields_by_group.items():
            group = group_data["group"]
            group_fields = group_data["fields"]
            description = group.get_description(language_code)

            # Wrap each field with ProfileFieldWithBadges layout object
            wrapped_fields = [
                ProfileFieldWithBadges(field.field_key, profile_field=field)
                for field in group_fields
            ]

            fieldset = Fieldset(
                group_name,
                *wrapped_fields,
                css_class="profile-field-group",
            )
            if description:
                fieldset.legend_attrs = {"title": description}

            layout_elements.append(fieldset)

        layout_elements.append(
            FormActions(
                Submit("submit", _("Update Profile"), css_class="btn btn-primary"),
                Cancel(),
            ),
        )

        self.helper.add_layout(Layout(*layout_elements))

    def clean(self):
        """Remove read-only field values for non-staff users."""
        cleaned_data = super().clean()

        # For read-only profile fields, if user is not staff, remove the value
        for profile_field in self._profile_fields:
            if profile_field.is_read_only:
                user = self.instance
                if not (user and user.is_staff):
                    # Remove the value from cleaned_data for security
                    cleaned_data.pop(profile_field.field_key, None)

        return cleaned_data

    def clean_profile_picture(self):
        """Validate profile picture file size and format."""
        picture = self.cleaned_data.get("profile_picture")

        if picture:
            # Check file size (5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if picture.size > max_size:
                raise ValidationError(
                    _("File size must be no more than 5MB. Your file is %(size).1fMB."),
                    params={"size": picture.size / (1024 * 1024)},
                    code="file_too_large",
                )

        return picture

    def save(self, commit=True):  # noqa: FBT002
        """Save user model and profile field responses."""
        user = super().save(commit=False)

        if commit:
            user.save()

            # Save profile field responses in a transaction
            with transaction.atomic():
                for profile_field in self._profile_fields:
                    field_key = profile_field.field_key
                    value = self.cleaned_data.get(field_key)

                    if value or value in (0, []):
                        # Value exists or is zero or empty list
                        if value or value == 0:
                            # Non-empty value: create or update response
                            response, _created = (
                                ProfileFieldResponse.objects.get_or_create(
                                    user=user,
                                    profile_field=profile_field,
                                )
                            )
                            response.set_value(value)
                            response.save()
                        else:
                            # Empty value: delete response if exists
                            ProfileFieldResponse.objects.filter(
                                user=user,
                                profile_field=profile_field,
                            ).delete()
                    else:
                        # No value: delete response if exists
                        ProfileFieldResponse.objects.filter(
                            user=user,
                            profile_field=profile_field,
                        ).delete()

        return user
