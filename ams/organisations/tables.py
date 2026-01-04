from django.template.loader import render_to_string
from django.urls import reverse
from django_tables2 import TemplateColumn
from django_tables2.columns import Column
from django_tables2.columns import DateColumn
from django_tables2.tables import Table

from ams.memberships.models import OrganisationMembership
from ams.organisations.models import OrganisationMember
from ams.utils.tables import MembershipStatusBadgeColumn
from ams.utils.tables import MemberStatusBadgeColumn


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
    status = MemberStatusBadgeColumn(
        accessor="is_active",
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

    def __init__(self, *args, request=None, organisation=None, **kwargs):
        """Initialize with request and organisation for action buttons."""
        super().__init__(*args, **kwargs)
        self.request = request
        self.organisation = organisation

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

    def render_actions(self, record):
        """Render actions column with role management buttons."""

        # Don't show actions for the current user (they should use "Leave Organisation")
        if self.request and record.user == self.request.user:
            return ""

        # For pending invites, show revoke action
        if not record.is_active():
            context = {
                "member": record,
                "organisation": self.organisation,
                "revoke_invite_url": reverse(
                    "organisations:revoke_invite",
                    kwargs={
                        "uuid": self.organisation.uuid,
                        "member_uuid": record.uuid,
                    },
                ),
            }
            return render_to_string(
                "organisations/snippets/pending_invite_actions.html",
                context,
                request=self.request,
            )

        # Build the context for rendering action buttons for active members
        context = {
            "member": record,
            "organisation": self.organisation,
            "remove_url": reverse(
                "organisations:remove_member",
                kwargs={
                    "uuid": self.organisation.uuid,
                    "member_uuid": record.uuid,
                },
            ),
        }

        # Add role management URLs based on current role
        if record.role == OrganisationMember.Role.MEMBER:
            context["make_admin_url"] = reverse(
                "organisations:make_admin",
                kwargs={
                    "uuid": self.organisation.uuid,
                    "member_uuid": record.uuid,
                },
            )
        else:  # ADMIN
            context["revoke_admin_url"] = reverse(
                "organisations:revoke_admin",
                kwargs={
                    "uuid": self.organisation.uuid,
                    "member_uuid": record.uuid,
                },
            )

        return render_to_string(
            "organisations/snippets/member_action_buttons.html",
            context,
            request=self.request,
        )


class OrganisationMembershipTable(Table):
    """Table for displaying memberships within an organisation detail page."""

    membership = Column(
        accessor="membership_option__name",
        verbose_name="Membership",
    )
    duration = Column(
        accessor="membership_option__duration_display",
        verbose_name="Duration",
        orderable=False,
    )
    status = MembershipStatusBadgeColumn(
        verbose_name="Status",
        empty_values=(),
        orderable=False,
    )
    start_date = DateColumn(
        accessor="start_date",
        verbose_name="Start Date",
    )
    expiry_date = DateColumn(
        accessor="expiry_date",
        verbose_name="Expires Date",
    )
    seats = Column(
        verbose_name="Seats",
        accessor="seats_summary",
        orderable=False,
    )
    invoice = TemplateColumn(
        template_name="users/tables/invoice_column.html",
        accessor="invoice",
        verbose_name="Invoice",
    )

    class Meta:
        model = OrganisationMembership
        fields = (
            "membership",
            "duration",
            "status",
            "start_date",
            "expiry_date",
            "seats",
            "invoice",
        )
        order_by = ("-start_date",)
