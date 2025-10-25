from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django.forms import CharField
from django.forms import EmailField
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from .models import User


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
