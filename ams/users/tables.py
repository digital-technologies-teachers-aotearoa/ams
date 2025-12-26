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


class OrganisationMemberTable(Table):
    """Table for displaying members within an organisation detail page."""

    name = Column(
        verbose_name="Name",
        empty_values=(),
        order_by=("user__first_name", "user__last_name"),
    )
    email = Column(
        verbose_name="Email",
        empty_values=(),
        orderable=False,
    )
    status = Column(
        verbose_name="Status",
        empty_values=(),
        orderable=False,
    )
    join_date = DateColumn(
        accessor="accepted_datetime",
        verbose_name="Join Date",
    )
    role = Column(
        accessor="role",
        verbose_name="Role",
    )
    actions = Column(
        verbose_name="Actions",
        empty_values=(),
        orderable=False,
    )

    class Meta:
        model = OrganisationMember
        fields = (
            "name",
            "email",
            "status",
            "join_date",
            "role",
            "actions",
        )
        order_by = ("-accepted_datetime",)

    def render_name(self, record):
        """Render the member's full name or invite email."""
        if record.user:
            return record.user.get_full_name()
        return "—"

    def render_email(self, record):
        """Render the member's email or invite email."""
        if record.user:
            return record.user.email
        return record.invite_email

    def render_status(self, record):
        """Render the member's status (Active or Invited)."""
        if record.is_active():
            return "Active"
        return "Invited"

    def render_actions(self, record):
        """Render actions column (empty for now as per step 4)."""
        return ""
