from typing import Any

from dateutil.relativedelta import relativedelta
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


def decompose_membership_duration(duration: relativedelta) -> tuple[int, str]:
    # Assumes duration can be represented as an integer of days, months, weeks or years
    if duration.years and duration.months == 0 and duration.days == 0:
        return duration.years, "years"
    if duration.months and duration.days == 0:
        return duration.months, "months"
    if duration.days % 7 == 0:
        return duration.days // 7, "weeks"
    return duration.days, "days"


def compose_membership_duration(num: int, unit: str) -> relativedelta | None:
    if unit == "days":
        return relativedelta(days=num)
    if unit == "weeks":
        return relativedelta(days=num * 7)
    if unit == "months":
        return relativedelta(months=num)
    if unit == "years":
        return relativedelta(years=num)
    return None


def format_membership_duration(duration: relativedelta) -> Any:
    count, unit = decompose_membership_duration(duration)

    if count == 1 and unit.endswith("s"):
        unit = unit[:-1]

    translated_unit = _(unit)

    return format_lazy("{} {}", count, translated_unit)
