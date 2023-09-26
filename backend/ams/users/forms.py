from datetime import date
from typing import Any, Dict, List, Tuple

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.forms import (
    CharField,
    ChoiceField,
    DateField,
    EmailField,
    Form,
    ModelChoiceField,
    ModelForm,
    PasswordInput,
    RadioSelect,
    ValidationError,
)
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from .models import (
    MembershipOption,
    MembershipOptionType,
    Organisation,
    OrganisationType,
)


def format_membership_duration_in_months(duration: relativedelta) -> Any:
    # NOTE: assumes duration measured in months and/or years
    months_count = duration.months + duration.years * 12
    months_unit = _("month") if months_count == 1 else _("months")

    return format_lazy("{} {}", months_count, months_unit)


def get_individual_membership_options() -> List[Tuple[str, str]]:
    return [
        (
            option.name,
            format_lazy("${} {} {}", option.cost, _("for"), format_membership_duration_in_months(option.duration)),
        )
        for option in MembershipOption.objects.filter(type=MembershipOptionType.INDIVIDUAL).order_by("id")
    ]


class MembershipOptionRadioSelect(RadioSelect):
    template_name = "membership_option_radio_select.html"


class AddUserMembershipForm(Form):
    start_date = DateField(label=_("Start Date"))
    membership_option = ChoiceField(
        label=_("Membership"), widget=MembershipOptionRadioSelect, choices=get_individual_membership_options
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_start_date(self) -> date:
        cleaned_data = super().clean()

        start_date: date = cleaned_data.get("start_date")

        # Validate that start date doesn't overlap with an existing non-cancelled membership
        latest_membership = self.user.get_latest_membership()
        if latest_membership and latest_membership.expiry_date() > start_date:
            raise ValidationError(_("A new membership can not overlap with an existing membership"))

        return start_date


class IndividualRegistrationForm(Form):
    email = EmailField(label=_("Email"))
    confirm_email = CharField(label=_("Confirm Email"))
    first_name = CharField(label=_("First Name"), max_length=255)
    last_name = CharField(label=_("Last Name"), max_length=255)
    password = CharField(label=_("Password"), widget=PasswordInput(), validators=[validate_password])
    confirm_password = CharField(label=_("Confirm Password"), widget=PasswordInput())
    membership_option = ChoiceField(widget=MembershipOptionRadioSelect, choices=get_individual_membership_options)

    def clean(self) -> Dict[str, Any]:
        cleaned_data: Dict[str, Any] = super().clean()

        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")

        if email:
            if email != confirm_email:
                self.add_error("confirm_email", _("The two email fields didn't match."))
            elif User.objects.filter(email=email).exists():
                self.add_error("email", _("A user with this email address already exists."))

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and password != confirm_password:
            self.add_error("confirm_password", _("The two password fields didn't match."))

        return cleaned_data


class EditUserProfileForm(ModelForm):
    username = CharField(label=_("Email"), disabled=True)
    first_name = CharField(label=_("First Name"), max_length=255)
    last_name = CharField(label=_("Last Name"), max_length=255)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]


class NameModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj: Any) -> str:
        name: str = obj.name
        return name


class OrganisationForm(ModelForm):
    type = NameModelChoiceField(queryset=OrganisationType.objects.order_by("id"), required=True, empty_label="")

    class Meta:
        model = Organisation
        fields = ["name", "type", "postal_address", "office_phone"]
