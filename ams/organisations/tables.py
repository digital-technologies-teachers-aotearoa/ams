from django_tables2.columns import Column
from django_tables2.columns import DateColumn
from django_tables2.tables import Table

from ams.organisations.models import OrganisationMember


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
