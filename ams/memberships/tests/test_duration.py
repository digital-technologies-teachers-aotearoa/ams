import pytest
from dateutil.relativedelta import relativedelta

import ams.memberships.duration as duration_module
from ams.memberships.duration import compose_membership_duration
from ams.memberships.duration import decompose_membership_duration
from ams.memberships.duration import format_membership_duration


@pytest.mark.parametrize(
    ("duration", "expected"),
    [
        (relativedelta(years=2), (2, "years")),
        (relativedelta(years=1), (1, "years")),
        (relativedelta(months=3), (3, "months")),
        (relativedelta(months=1), (1, "months")),
        (relativedelta(days=14), (2, "weeks")),
        (relativedelta(days=7), (1, "weeks")),
        (relativedelta(days=10), (10, "days")),
        (relativedelta(days=1), (1, "days")),
    ],
)
def test_decompose_membership_duration(duration, expected):
    assert decompose_membership_duration(duration) == expected


@pytest.mark.parametrize(
    ("num", "unit", "expected_duration"),
    [
        (5, "days", relativedelta(days=5)),
        (3, "weeks", relativedelta(days=21)),
        (4, "months", relativedelta(months=4)),
        (2, "years", relativedelta(years=2)),
    ],
)
def test_compose_membership_duration(num, unit, expected_duration):
    duration = compose_membership_duration(num, unit)
    assert isinstance(duration, relativedelta)
    # relativedelta equality compares components
    assert duration == expected_duration
    # Round trip
    decomposed = decompose_membership_duration(duration)
    # For weeks the unit returned should be "weeks"
    if unit == "weeks":
        assert decomposed == (num, "weeks")
    else:
        assert decomposed == (num, unit)


def test_compose_membership_duration_invalid_unit():
    assert compose_membership_duration(5, "invalid") is None


@pytest.mark.parametrize(
    ("duration", "expected_str"),
    [
        (relativedelta(days=1), "1 day"),
        (relativedelta(days=2), "2 days"),
        (relativedelta(days=7), "1 week"),
        (relativedelta(days=14), "2 weeks"),
        (relativedelta(months=1), "1 month"),
        (relativedelta(months=3), "3 months"),
        (relativedelta(years=1), "1 year"),
        (relativedelta(years=5), "5 years"),
    ],
)
def test_format_membership_duration_monkeypatched_translation(
    duration,
    expected_str,
    monkeypatch,
):
    # Avoid needing Django settings: neutralize translation
    monkeypatch.setattr(duration_module, "_", lambda s: s)
    result = format_membership_duration(duration)
    assert str(result) == expected_str


@pytest.mark.parametrize(
    ("num", "unit"),
    [
        (1, "days"),
        (2, "days"),
        (1, "weeks"),
        (3, "weeks"),
        (1, "months"),
        (6, "months"),
        (1, "years"),
        (4, "years"),
    ],
)
def test_round_trip(num, unit):
    duration = compose_membership_duration(num, unit)
    assert duration is not None
    decomposed_num, decomposed_unit = decompose_membership_duration(duration)
    # For singular formatting logic, decompose always returns plural units
    if unit == "weeks":
        assert decomposed_unit == "weeks"
    else:
        assert decomposed_unit == unit
    assert decomposed_num == num
