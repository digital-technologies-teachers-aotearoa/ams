from dateutil.relativedelta import relativedelta
from django.test import TestCase

from ..forms import (
    compose_membership_duration,
    decompose_membership_duration,
    format_membership_duration,
)


class MembershipDurationTests(TestCase):
    def test_decompose_membership_duration(self) -> None:
        self.assertEqual((1, "days"), decompose_membership_duration(relativedelta(days=1)))
        self.assertEqual((2, "weeks"), decompose_membership_duration(relativedelta(days=14)))
        self.assertEqual((3, "months"), decompose_membership_duration(relativedelta(months=3)))
        self.assertEqual((4, "years"), decompose_membership_duration(relativedelta(years=4)))

    def test_create_membership_duration(self) -> None:
        self.assertEqual(relativedelta(days=1), compose_membership_duration(1, "days"))
        self.assertEqual(relativedelta(days=14), compose_membership_duration(2, "weeks"))
        self.assertEqual(relativedelta(months=3), compose_membership_duration(3, "months"))
        self.assertEqual(relativedelta(years=4), compose_membership_duration(4, "years"))

    def test_format_membership_duration(self) -> None:
        self.assertEqual("1 day", format_membership_duration(relativedelta(days=1)))
        self.assertEqual("2 days", format_membership_duration(relativedelta(days=2)))
        self.assertEqual("1 week", format_membership_duration(relativedelta(days=7)))
        self.assertEqual("3 weeks", format_membership_duration(relativedelta(days=21)))
        self.assertEqual("1 month", format_membership_duration(relativedelta(months=1)))
        self.assertEqual("1 year", format_membership_duration(relativedelta(months=12)))
        self.assertEqual("2 years", format_membership_duration(relativedelta(years=2)))
