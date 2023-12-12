from datetime import date, datetime
from typing import Any

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, DateColumn, Table, TemplateColumn

from .forms import format_membership_duration
from .models import (
    MembershipOption,
    Organisation,
    OrganisationMember,
    OrganisationMembership,
    UserMembership,
)


def full_name_or_username(user: User) -> str:
    full_name: str = user.get_full_name()
    if not full_name:
        username: str = user.username
        return username
    return full_name


class AdminUserTable(Table):
    full_name = Column(
        accessor="first_name", order_by=("first_name", "last_name"), verbose_name=_("Full Name"), empty_values=()
    )
    email = Column(verbose_name=_("Email"))
    active = Column(accessor="is_active", verbose_name=_("Active"))
    actions = TemplateColumn(verbose_name=_("Actions"), template_name="admin_user_actions.html", orderable=False)

    def render_full_name(self, value: str, record: User) -> str:
        return full_name_or_username(record)

    def render_active(self, value: bool, record: User) -> Any:
        if value:
            return _("Active")
        return _("Not Active")

    class Meta:
        fields = ("full_name", "email")
        order_by = ("full_name", "email", "active")
        model = User


class AdminUserMembershipTable(Table):
    full_name = Column(
        accessor="user__first_name",
        order_by=("user__first_name", "user__last_name"),
        verbose_name=_("Full Name"),
        empty_values=(),
    )
    membership = Column(accessor="membership_option__name", verbose_name=_("Membership"))
    duration = Column(accessor="membership_option__duration", verbose_name=_("Duration"))
    status = Column(
        verbose_name=_("Status"),
        accessor="approved_datetime",
        empty_values=[],
    )
    start_date = DateColumn(verbose_name=_("Start Date"), short=True)
    approved_date = DateColumn(verbose_name=_("Approved Date"), accessor="approved_datetime", short=True)

    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="admin_user_membership_actions.html", orderable=False
    )

    def render_full_name(self, value: str, record: UserMembership) -> str:
        return full_name_or_username(record.user)

    def render_status(self, value: datetime, record: UserMembership) -> Any:
        return record.status().label

    def render_duration(self, value: relativedelta, record: UserMembership) -> Any:
        return format_membership_duration(value)

    class Meta:
        fields = ("full_name", "membership", "duration", "status", "start_date", "approved_date")
        order_by = (
            "full_name",
            "membership",
            "duration",
            "status",
            "start_date",
            "approved_date",
            "cancelled_datetime",
        )
        model = UserMembership


class UserDetailMembershipTable(Table):
    membership = Column(accessor="membership_option__name", verbose_name=_("Membership"))
    duration = Column(accessor="membership_option__duration", verbose_name=_("Duration"))
    status = Column(
        verbose_name=_("Status"),
        accessor="approved_datetime",
        empty_values=[],
    )
    start_date = DateColumn(verbose_name=_("Start Date"), short=True)
    approved_date = DateColumn(verbose_name=_("Approved Date"), accessor="approved_datetime", short=True)
    actions = TemplateColumn(verbose_name=_("Actions"), template_name="user_membership_actions.html", orderable=False)

    def render_status(self, value: datetime, record: UserMembership) -> Any:
        return record.status().label

    def render_duration(self, value: relativedelta, record: UserMembership) -> Any:
        return format_membership_duration(value)

    class Meta:
        fields = ("membership", "duration", "status", "start_date", "approved_date")
        order_by = ("membership", "duration", "status", "start_date", "approved_date", "cancelled_datetime")
        model = UserMembership


class AdminUserDetailMembershipTable(UserDetailMembershipTable):
    # NOTE: this uses the same actions template as AdminUserMembershipTable
    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="admin_user_membership_actions.html", orderable=False
    )


class AdminMembershipOptionTable(Table):
    name = Column(verbose_name=_("Name"))
    type = Column(verbose_name=_("Type"))
    duration = Column(verbose_name=_("Duration"))
    cost = Column(verbose_name=_("Cost"))
    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="admin_membership_option_actions.html", orderable=False
    )

    def render_duration(self, value: relativedelta, record: MembershipOption) -> Any:
        return format_membership_duration(value)

    class Meta:
        fields = ("name", "type", "duration", "cost")
        order_by = ("name", "type")
        model = MembershipOption


class AdminOrganisationTable(Table):
    name = Column(verbose_name=_("Name"))
    type = Column(accessor="type__name", verbose_name=_("Type"))
    telephone = Column(verbose_name=_("Telephone"))
    email = Column(verbose_name=_("Email"))
    contact_name = Column(verbose_name=_("Contact Name"))
    city = Column(verbose_name=_("City"))
    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="admin_organisation_actions.html", orderable=False
    )

    class Meta:
        fields = ("name", "type", "telephone", "email", "contact_name", "city")
        order_by = ("name", "type")
        model = Organisation


class OrganisationMemberTable(Table):
    name = Column(
        verbose_name=_("Name"),
        accessor="user__first_name",
        order_by=("user__first_name", "user__last_name"),
    )
    email = Column(verbose_name=_("Email"), accessor="invite_email")
    status = Column(verbose_name=_("Status"), accessor="accepted_datetime", empty_values=[], orderable=False)
    join_date = DateColumn(verbose_name=_("Join Date"), accessor="accepted_datetime", short=True)
    role = Column(verbose_name=_("Role"), accessor="is_admin", order_by=("is_admin", "-accepted_datetime"))
    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="organisation_member_actions.html", orderable=False
    )

    def render_name(self, value: str, record: UserMembership) -> str:
        return full_name_or_username(record.user)

    def render_email(self, value: str, record: OrganisationMember) -> Any:
        # Show user's current email if there is a user, otherwise show the invite email
        if record.user:
            return record.user.email
        return value

    def render_status(self, value: datetime, record: OrganisationMember) -> Any:
        if record.is_active():
            return _("Active")
        return _("Invited")

    def render_role(self, value: bool, record: OrganisationMember) -> Any:
        if value:
            return _("Admin")
        if record.is_active():
            return _("Member")
        return ""

    class Meta:
        fields = ("name", "email", "status", "join_date", "role")
        order_by = ("email",)
        model = OrganisationMember


class OrganisationMembershipTable(Table):
    membership = Column(accessor="membership_option__name", verbose_name=_("Membership"))
    duration = Column(accessor="membership_option__duration", verbose_name=_("Duration"))
    status = Column(verbose_name=_("Status"), accessor="start_date", empty_values=[], orderable=False)
    start_date = DateColumn(verbose_name=_("Start Date"), short=True)
    expiry_date = DateColumn(verbose_name=_("Expires Date"), accessor="start_date", short=True, orderable=False)
    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="organisation_membership_actions.html", orderable=False
    )

    def render_status(self, value: date, record: OrganisationMembership) -> Any:
        return record.status().label

    def render_expiry_date(self, value: date, record: OrganisationMembership) -> Any:
        return date_format(record.expiry_date(), format=settings.SHORT_DATE_FORMAT)

    def render_duration(self, value: relativedelta, record: OrganisationMembership) -> Any:
        return format_membership_duration(value)

    class Meta:
        fields = ("membership", "duration", "status", "start_date")
        order_by = ("membership", "duration", "status", "start_date", "expiry_date")
        model = OrganisationMembership
