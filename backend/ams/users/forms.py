from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import UploadedFile
from django.forms import (
    CharField,
    ChoiceField,
    DateField,
    DecimalField,
    EmailField,
    Form,
    ImageField,
    IntegerField,
    ModelChoiceField,
    ModelForm,
    MultiValueField,
    MultiWidget,
    PasswordInput,
    RadioSelect,
    Select,
    TextInput,
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


def decompose_membership_duration(duration: relativedelta) -> Tuple[int, str]:
    # Assumes duration can be represented as an integer number of either days, months, weeks or years
    if duration.years and duration.months == 0 and duration.days == 0:
        return duration.years, "years"
    elif duration.months and duration.days == 0:
        return duration.months, "months"
    elif duration.days % 7 == 0:
        return duration.days // 7, "weeks"
    return duration.days, "days"


def compose_membership_duration(num: int, unit: str) -> Optional[relativedelta]:
    if unit == "days":
        return relativedelta(days=num)
    elif unit == "weeks":
        return relativedelta(days=num * 7)
    elif unit == "months":
        return relativedelta(months=num)
    elif unit == "years":
        return relativedelta(years=num)
    return None


def format_membership_duration(duration: relativedelta) -> Any:
    count, unit = decompose_membership_duration(duration)

    if count == 1 and unit.endswith("s"):
        unit = unit[:-1]

    translated_unit = _(unit)

    return format_lazy("{} {}", count, translated_unit)


def get_membership_options(option_type: Any) -> List[Tuple[str, str]]:
    membership_options = MembershipOption.objects.filter(type=option_type).order_by("id")
    return [
        (
            option.name,
            format_lazy("${} {} {}", option.cost, _("for"), format_membership_duration(option.duration)),
        )
        for option in membership_options
    ]


def get_individual_membership_options() -> List[Tuple[str, str]]:
    return get_membership_options(option_type=MembershipOptionType.INDIVIDUAL)


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
    email = EmailField(label=_("Email"))

    class Meta:
        model = Organisation
        fields = [
            "name",
            "type",
            "telephone",
            "email",
            "contact_name",
            "street_address",
            "suburb",
            "city",
            "postal_code",
            "postal_address",
        ]


class MembershipDurationWidget(MultiWidget):
    def __init__(self, choices: List[Tuple[str, str]], attrs: Optional[Dict[str, Any]] = None) -> None:
        widgets = (
            TextInput(attrs=attrs),
            Select(attrs=attrs, choices=choices),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value: Optional[relativedelta]) -> List[Any]:
        if value:
            unit, count = decompose_membership_duration(value)
            return [unit, count]
        return [None, None]


class MembershipDurationField(MultiValueField):
    choices = [("days", _("Days")), ("weeks", _("Weeks")), ("months", _("Months")), ("years", _("Years"))]

    def __init__(self, *args: Any, **kwargs: Any):
        fields = (
            IntegerField(min_value=1),
            ChoiceField(choices=self.choices),
        )
        super().__init__(fields, *args, **kwargs)
        self.widget = MembershipDurationWidget(choices=self.choices, attrs={"class": "membership-duration"})

    def compress(self, data_list: List[Any]) -> Optional[relativedelta]:
        if data_list:
            num, unit = data_list
            if num is not None and unit:
                num = int(num)
                return compose_membership_duration(num, unit)
        return None


class MembershipOptionForm(ModelForm):
    name = CharField(label=_("Name"), max_length=255)
    type = ChoiceField(
        label=_("Type"),
        choices=[
            (MembershipOptionType.INDIVIDUAL.value, MembershipOptionType.INDIVIDUAL.label),  # type: ignore
            (MembershipOptionType.ORGANISATION.value, MembershipOptionType.ORGANISATION.label),  # type: ignore
        ],
    )
    duration = MembershipDurationField(label=_("Duration"))
    cost = DecimalField(label=_("Cost"))

    class Meta:
        model = MembershipOption
        fields = ["name", "type", "duration", "cost"]


class UploadProfileImageForm(Form):
    profile_image_file = ImageField()

    def clean_profile_image_file(self) -> UploadedFile:
        profile_image_file = self.cleaned_data["profile_image_file"]

        if profile_image_file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise ValidationError("Image should be valid JPG, PNG or GIF.")

        if profile_image_file.size > 1048576:
            raise ValidationError("Image should not exceed 1MB in size.")

        return profile_image_file
