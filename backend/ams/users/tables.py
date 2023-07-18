from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, DateColumn, Table, TemplateColumn

from .forms import format_membership_duration_in_months
from .models import UserMembership


class AdminUserTable(Table):
    full_name = Column(accessor="first_name", order_by=("first_name", "last_name"), verbose_name=_("Full Name"))
    email = Column(verbose_name=_("Email"))
    actions = TemplateColumn(verbose_name=_("Actions"), template_name="admin_user_actions.html", orderable=False)

    def render_full_name(self, value: str, record: User) -> str:
        full_name: str = record.get_full_name()
        return full_name

    class Meta:
        fields = ("full_name", "email")
        order_by = ("full_name", "email")
        model = User


class AdminUserMembershipTable(Table):
    full_name = Column(
        accessor="user__first_name", order_by=("user__first_name", "user__last_name"), verbose_name=_("Full Name")
    )
    membership = Column(accessor="membership_option__name", verbose_name=_("Membership"))
    duration = Column(accessor="membership_option__duration", verbose_name=_("Duration"))
    status = Column(
        verbose_name=_("Status"),
        accessor="approved_datetime",
        empty_values=[],
    )
    start_date = DateColumn(verbose_name=_("Start Date"), accessor="created_datetime", short=True)
    approved_date = DateColumn(verbose_name=_("Approved Date"), accessor="approved_datetime", short=True)
    actions = TemplateColumn(
        verbose_name=_("Actions"), template_name="admin_user_membership_actions.html", orderable=False
    )

    def render_full_name(self, value: str, record: UserMembership) -> str:
        full_name: str = record.user.get_full_name()
        return full_name

    def render_status(self, value: datetime, record: UserMembership) -> Any:
        if record.approved_datetime:
            return _("Approved")
        return _("Pending")

    def render_duration(self, value: relativedelta, record: UserMembership) -> Any:
        return format_membership_duration_in_months(value)

    class Meta:
        fields = ("full_name", "membership", "duration", "status", "start_date", "approved_date")
        order_by = ("full_name", "membership", "duration", "status", "start_date", "approved_date")
        model = UserMembership
