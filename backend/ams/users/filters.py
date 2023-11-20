from django.conf import settings
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_filters import ChoiceFilter, FilterSet


class UserMembershipFilter(FilterSet):
    STATUS_FILTER_CHOICES = (
        ("pending", _("Pending")),
        ("active", _("Active")),
        ("expired", _("Expired")),
        ("cancelled", _("Cancelled")),
    )

    def filter_membership_status(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        time_zone = settings.TIME_ZONE

        return queryset.extra(
            where=[
                """
                CASE WHEN cancelled_datetime IS NOT NULL THEN
                    'cancelled'

                WHEN CURRENT_TIMESTAMP >= (start_date AT TIME ZONE %s)::timestamptz + (
                        SELECT duration
                        FROM users_membershipoption
                        WHERE users_membershipoption.id = membership_option_id) THEN
                    'expired'

                WHEN approved_datetime IS NULL OR (start_date AT TIME ZONE %s)::timestamptz > CURRENT_TIMESTAMP THEN
                    'pending'
                ELSE
                    'active'
                END = %s
            """
            ],
            params=[time_zone, time_zone, value],
        )

    status = ChoiceFilter(
        label=_("Status"),
        empty_label=_("All Statuses"),
        choices=STATUS_FILTER_CHOICES,
        method="filter_membership_status",
    )
