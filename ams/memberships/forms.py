from typing import Any

from dateutil.relativedelta import relativedelta
from django.forms import CharField
from django.forms import ChoiceField
from django.forms import DecimalField
from django.forms import IntegerField
from django.forms import ModelForm
from django.forms import MultiValueField
from django.forms import MultiWidget
from django.forms import Select
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from ams.memberships.duration import compose_membership_duration
from ams.memberships.duration import decompose_membership_duration

from .models import MembershipOption
from .models import MembershipOptionType


class MembershipDurationWidget(MultiWidget):
    def __init__(
        self,
        choices: list[tuple[str, str]],
        attrs: dict[str, Any] | None = None,
    ) -> None:
        widgets = (
            TextInput(attrs=attrs),
            Select(attrs=attrs, choices=choices),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value: relativedelta | None) -> list[Any]:
        if value:
            unit, count = decompose_membership_duration(value)
            return [unit, count]
        return [None, None]


class MembershipDurationField(MultiValueField):
    choices = [
        ("days", _("Days")),
        ("weeks", _("Weeks")),
        ("months", _("Months")),
        ("years", _("Years")),
    ]

    def __init__(self, *args: Any, **kwargs: Any):
        fields = (
            IntegerField(min_value=1),
            ChoiceField(choices=self.choices),
        )
        super().__init__(fields, *args, **kwargs)
        self.widget = MembershipDurationWidget(
            choices=self.choices,
            attrs={"class": "membership-duration"},
        )

    def compress(self, data_list: list[Any]) -> relativedelta | None:
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
            (
                MembershipOptionType.INDIVIDUAL.value,
                MembershipOptionType.INDIVIDUAL.label,
            ),
        ],
    )
    duration = MembershipDurationField(label=_("Duration"))
    cost = DecimalField(label=_("Cost"))

    class Meta:
        model = MembershipOption
        fields = ["name", "type", "duration", "cost"]
