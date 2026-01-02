from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_tables2 import TemplateColumn
from django_tables2.columns import Column
from django_tables2.columns import DateColumn
from django_tables2.tables import Table

from ams.memberships.models import IndividualMembership
from ams.organisations.models import OrganisationMember
from ams.utils.permissions import organisation_has_active_membership
from ams.utils.tables import MembershipStatusBadgeColumn


class MembershipTable(Table):
    membership = Column(
        accessor="membership_option__name",
        verbose_name="Membership",
    )
    duration = Column(
        accessor="membership_option__duration_display",
        verbose_name="Duration",
    )
    status = MembershipStatusBadgeColumn(accessor="status", verbose_name="Status")
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


class PendingInvitationTable(Table):
    """Table for displaying pending organisation invitations."""

    organisation_name = Column(
        accessor="organisation__name",
        verbose_name="Organisation",
    )
    role = Column(
        accessor="role",
        verbose_name="Role",
    )
    invited_date = DateColumn(
        accessor="created_datetime",
        verbose_name="Invited Date",
    )
    actions = TemplateColumn(
        template_name="users/tables/pending_invitation_actions_column.html",
        verbose_name="Actions",
    )

    class Meta:
        model = OrganisationMember
        fields = (
            "organisation_name",
            "role",
            "invited_date",
            "actions",
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
    membership = Column(
        empty_values=(),
        verbose_name="Membership",
    )
    actions = TemplateColumn(
        template_name="users/tables/organisation_actions_column.html",
        verbose_name="Actions",
    )

    def render_membership(self, record):
        """Render the membership status badge."""
        return mark_safe(  # noqa: S308
            render_to_string(
                "users/tables/organisation_membership_column.html",
                {
                    "active_membership": organisation_has_active_membership(
                        record.organisation,
                    ),
                },
            ),
        )

    class Meta:
        model = OrganisationMember
        fields = (
            "organisation_name",
            "role",
            "join_date",
            "membership",
            "actions",
        )
