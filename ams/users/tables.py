from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_tables2 import TemplateColumn
from django_tables2.columns import Column
from django_tables2.columns import DateColumn
from django_tables2.tables import Table

from ams.memberships.models import IndividualMembership
from ams.users.models import OrganisationMember


class StatusBadgeColumn(Column):
    def render(self, value):
        return mark_safe(  # noqa: S308
            render_to_string("snippets/status_badge.html", {"status": value}),
        )


class MembershipTable(Table):
    membership = Column(
        accessor="membership_option__name",
        verbose_name="Membership",
    )
    duration = Column(
        accessor="membership_option__duration_display",
        verbose_name="Duration",
    )
    status = StatusBadgeColumn(accessor="status", verbose_name="Status")
    start_date = DateColumn(verbose_name="Start Date")
    expiry_date = DateColumn(verbose_name="End Date")
    invoice = TemplateColumn(
        template_name="users/tables/invoice_column.html",
        accessor="invoice",
        verbose_name="Invoice",
    )

    class Meta:
        model = IndividualMembership
        fields = (
            "membership",
            "duration",
            "status",
            "start_date",
            "expiry_date",
            "invoice",
        )


class OrganisationTable(Table):
    organisation_name = Column(
        accessor="organisation__name",
        verbose_name="Organisation",
    )
    role = Column(
        accessor="role",
        verbose_name="Role",
    )
    join_date = DateColumn(
        accessor="accepted_datetime",
        verbose_name="Join Date",
    )
    has_membership = TemplateColumn(
        template_name="users/tables/organisation_membership_column.html",
        verbose_name="Organisation Membership",
    )
    actions = TemplateColumn(
        template_name="users/tables/organisation_actions_column.html",
        verbose_name="Actions",
    )

    class Meta:
        model = OrganisationMember
        fields = (
            "organisation_name",
            "role",
            "join_date",
            "has_membership",
            "actions",
        )
