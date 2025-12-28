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
from django.forms import Form
from django.forms import ImageField
from django.forms import ModelForm
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from ams.users.models import Organisation
from ams.users.models import OrganisationMember
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


class InviteOrganisationMemberForm(Form):
    """
    Form for inviting members to an organisation.
    Validates that the email doesn't already belong to an active or invited member.
    """

    email = EmailField(
        label=_("Email"),
        required=True,
        validators=[EmailValidator()],
        help_text=_("Enter the email address of the person you'd like to invite."),
        widget=TextInput(
            attrs={
                "placeholder": _("member@example.com"),
                "autocomplete": "email",
            },
        ),
    )

    def __init__(self, organisation, cancel_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Validate organisation parameter
        if organisation is None:
            message = "organisation is required and cannot be None"
            raise ValueError(message)

        if not isinstance(organisation, Organisation):
            message = (
                f"organisation must be an instance of Organisation, "
                f"got {type(organisation).__name__}"
            )
            raise TypeError(message)

        self.organisation = organisation
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_layout(
            Layout(
                "email",
                FormActions(
                    Submit("submit", _("Send Invite"), css_class="btn btn-primary"),
                    Cancel(cancel_url),
                ),
            ),
        )

    def clean_email(self):
        """Validate that the email is not already a member of the organisation."""
        email = self.cleaned_data.get("email")
        if not email:
            return email

        # Normalize email to lowercase
        email = email.lower()

        if not self.organisation:
            return email

        # Check if user or invite_email already exists for this organisation
        existing_member = OrganisationMember.objects.filter(
            organisation=self.organisation,
        ).filter(
            # Check both user email and invite_email
            user__email=email,
        ) | OrganisationMember.objects.filter(
            organisation=self.organisation,
            invite_email=email,
        )

        if existing_member.exists():
            raise ValidationError(
                _(
                    "This email address is already associated with a member "
                    "of this organisation.",
                ),
                code="duplicate_member",
            )

        return email
