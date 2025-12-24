from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django.contrib.auth import forms as admin_forms
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.forms import CharField
from django.forms import EmailField
from django.forms import ImageField
from django.forms import ModelForm
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from ams.users.models import Organisation
from ams.users.models import User
from ams.utils.crispy_forms import Cancel


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
        fields = ("email",)
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
    Form for updating user profile information including profile picture.
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


class OrganisationForm(ModelForm):
    """
    Form for creating and editing organisations.
    Validates email format and ensures required fields are filled.
    """

    email = EmailField(
        label=_("Email"),
        required=True,
        validators=[EmailValidator()],
        help_text=_("Organisation contact email address."),
    )

    class Meta:
        model = Organisation
        fields = [
            "name",
            "telephone",
            "email",
            "contact_name",
            "postal_address",
            "postal_suburb",
            "postal_city",
            "postal_code",
            "street_address",
            "suburb",
            "city",
        ]

    def __init__(self, cancel_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        # Determine if we're creating or updating based on instance
        if self.instance and self.instance.pk:
            submit_text = _("Update Organisation")
        else:
            submit_text = _("Create Organisation")
        self.helper.add_layout(
            Layout(
                "name",
                "telephone",
                "contact_name",
                "email",
                Fieldset(
                    _("Physical address"),
                    "street_address",
                    "suburb",
                    "city",
                ),
                Fieldset(
                    _("Postal address"),
                    "postal_address",
                    "postal_suburb",
                    "postal_city",
                    "postal_code",
                ),
                FormActions(
                    Submit("submit", submit_text, css_class="btn btn-primary"),
                    Cancel(cancel_url),
                ),
            ),
        )

    def clean_email(self):
        """Validate that email is in correct format."""
        email = self.cleaned_data.get("email")
        if email:
            # EmailValidator already validates, convert to lowercase
            return email.lower()
        return email
