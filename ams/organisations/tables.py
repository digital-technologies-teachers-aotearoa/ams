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
        """Render actions column (empty for now as per step 4)."""
        return ""


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
        empty_values=(),
        orderable=False,
    )
    invoice = Column(
        verbose_name="Invoice",
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
        )
        order_by = ("-start_date",)

    def render_seats(self, record):
        """Render seats occupied vs limit."""
        if record.max_seats:
            return f"{record.occupied_seats} / {int(record.max_seats)}"
        return f"{record.occupied_seats} (Unlimited)"

    def render_invoice(self, record):
        """Render invoice number if available."""
        if record.invoice:
            return record.invoice.invoice_number
        return "—"
