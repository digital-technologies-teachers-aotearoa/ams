from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_tables2 import TemplateColumn
from django_tables2.columns import Column
from django_tables2.columns import DateColumn
from django_tables2.tables import Table

from ams.memberships.models import IndividualMembership
from ams.organisations.models import OrganisationMember
from ams.utils.tables import MembershipStatusBadgeColumn


class MembershipTable(Table):
    membership = Column(
        accessor="membership_option__name",
        # Translators: Column header — the membership plan the user is enrolled in
        verbose_name=_("Membership"),
    )
    duration = Column(
        accessor="membership_option__duration_display",
        # Translators: Column header — the length of the membership period
        verbose_name=_("Duration"),
    )
    status = MembershipStatusBadgeColumn(
        accessor="status",
        # Translators: Column header — current membership status (e.g. Active, Expired)
        verbose_name=_("Status"),
    )
    start_date = DateColumn(
        # Translators: Column header — the date the membership began
        verbose_name=_("Start Date"),
    )
    expiry_date = DateColumn(
        # Translators: Column header — the date the membership ends
        verbose_name=_("End Date"),
    )
    invoice = TemplateColumn(
        template_name="users/tables/invoice_column.html",
        # Translators: Column header — link to the billing invoice for this membership
        verbose_name=_("Invoice"),
        orderable=False,
    )
    actions = Column(
        # Translators: Column header — buttons to manage this membership (e.g. cancel)
        verbose_name=_("Actions"),
        empty_values=(),
        orderable=False,
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
            "actions",
        )

    def render_actions(self, record: IndividualMembership):
        """Render actions column with role management buttons."""

        # Build the context for rendering action buttons for active members
        context = {
            "can_cancel": record.can_cancel,
        }

        return render_to_string(
            "memberships/membership_actions_column.html",
            context,
        )


class PendingInvitationTable(Table):
    """Table for displaying pending organisation invitations."""

    organisation_name = Column(
        accessor="organisation__name",
        # Translators: Column header — organisation the user was invited to join
        verbose_name=_("Organisation"),
    )
    role = Column(
        accessor="role",
        # Translators: Column header — user's role in the organisation (Member/Admin)
        verbose_name=_("Role"),
    )
    invited_date = DateColumn(
        accessor="created_datetime",
        # Translators: Column header — the date the invitation was sent
        verbose_name=_("Invited Date"),
    )
    actions = TemplateColumn(
        template_name="users/tables/pending_invitation_actions_column.html",
        # Translators: Column header — buttons to accept or decline the invitation
        verbose_name=_("Actions"),
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
        # Translators: Column header — the name of the organisation the user belongs to
        verbose_name=_("Organisation"),
    )
    role = Column(
        accessor="role",
        # Translators: Column header — user's role in the organisation (Member/Admin)
        verbose_name=_("Role"),
    )
    join_date = DateColumn(
        accessor="accepted_datetime",
        # Translators: Column header — the date the user joined the organisation
        verbose_name=_("Join Date"),
    )
    membership = Column(
        empty_values=(),
        # Translators: Column header — the organisation's active membership plan
        verbose_name=_("Membership"),
    )
    actions = TemplateColumn(
        template_name="users/tables/organisation_actions_column.html",
        # Translators: Column header — buttons to manage the organisation membership
        verbose_name=_("Actions"),
    )

    def render_membership(self, record):
        """Render the membership status badge using annotated value."""
        return mark_safe(  # noqa: S308
            render_to_string(
                "users/tables/organisation_membership_column.html",
                {
                    "active_membership": record.org_has_active_membership,
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
