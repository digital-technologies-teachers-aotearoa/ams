import django_tables2 as tables
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from ams.memberships.models import IndividualMembership


class StatusBadgeColumn(tables.Column):
    def render(self, value):
        return mark_safe(  # noqa: S308
            render_to_string("snippets/status_badge.html", {"status": value}),
        )


class MembershipTable(tables.Table):
    membership = tables.Column(
        accessor="membership_option.name",
        verbose_name="Membership",
    )
    duration = tables.Column(
        accessor="membership_option.duration_display",
        verbose_name="Duration",
    )
    status = StatusBadgeColumn(accessor="status", verbose_name="Status")
    start_date = tables.Column(verbose_name="Start Date")
    approved_date = tables.Column(
        accessor="approved_datetime",
        verbose_name="Approved Date",
    )
    invoice = tables.Column(accessor="invoice", verbose_name="Invoice")

    class Meta:
        model = IndividualMembership
        fields = (
            "membership",
            "duration",
            "status",
            "start_date",
            "approved_date",
            "invoice",
        )
