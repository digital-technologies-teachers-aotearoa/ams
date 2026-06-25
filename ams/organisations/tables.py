from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
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
        # Translators: Column header — the member's full name
        verbose_name=_("Name"),
        empty_values=(),
        order_by=("user__first_name", "user__last_name"),
    )
    email = Column(
        # Translators: Column header — the member's email address
        verbose_name=_("Email"),
        empty_values=(),
        orderable=False,
    )
    status = MemberStatusBadgeColumn(
        accessor="is_active",
        # Translators: Column header — member account status (active/inactive)
        verbose_name=_("Status"),
        empty_values=(),
        orderable=False,
    )
    join_date = DateColumn(
        accessor="accepted_datetime",
        # Translators: Column header — the date the member joined the organisation
        verbose_name=_("Join Date"),
    )
    role = Column(
        accessor="role",
        # Translators: Column header — user's role in the organisation (Member/Admin)
        verbose_name=_("Role"),
    )
    actions = Column(
        # Translators: Column header — buttons to manage the member
        verbose_name=_("Actions"),
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

        # For pending invites (not accepted and not declined), show revoke action
        if (
            record.accepted_datetime is None
            and record.declined_datetime is None
            and record.revoked_datetime is None
        ):
            context = {
                "member": record,
                "organisation": self.organisation,
                "resend_invite_url": reverse(
                    "organisations:resend_invite",
                    kwargs={
                        "uuid": self.organisation.uuid,
                        "member_uuid": record.uuid,
                    },
                ),
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
        # Translators: Column header — the organisation's membership plan name
        verbose_name=_("Membership"),
    )
    duration = Column(
        accessor="membership_option__duration_display",
        # Translators: Column header — the length of the membership period
        verbose_name=_("Duration"),
        orderable=False,
    )
    status = MembershipStatusBadgeColumn(
        # Translators: Column header — current membership status (e.g. Active, Expired)
        verbose_name=_("Status"),
        empty_values=(),
        orderable=False,
    )
    start_date = DateColumn(
        accessor="start_date",
        # Translators: Column header — the date the membership began
        verbose_name=_("Start Date"),
    )
    expiry_date = DateColumn(
        accessor="expiry_date",
        # Translators: Column header — the date the membership expires
        verbose_name=_("Expires Date"),
    )
    seats = Column(
        # Translators: Column header — seat usage summary
        verbose_name=_("Seats"),
        accessor="seats_summary",
        orderable=False,
    )
    invoice = TemplateColumn(
        template_name="users/tables/invoice_column.html",
        # Translators: Column header — link to the billing invoice
        verbose_name=_("Invoice"),
        orderable=False,
    )
    actions = Column(
        # Translators: Column header — buttons to manage this membership
        verbose_name=_("Actions"),
        empty_values=(),
        orderable=False,
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
            "actions",
        )
        order_by = ("-start_date",)

    def render_actions(self, record: OrganisationMembership):
        """Render actions column with role management buttons."""

        # Build the context for rendering action buttons for active members
        context = {
            "can_cancel": record.can_cancel,
        }

        return render_to_string(
            "memberships/membership_actions_column.html",
            context,
        )
