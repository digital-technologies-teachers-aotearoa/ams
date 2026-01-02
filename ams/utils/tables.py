"""Reusable table utilities for django-tables2."""

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_tables2.columns import Column

from ams.memberships.models import OrganisationMembership


class MembershipStatusBadgeColumn(Column):
    """Column that renders membership status values."""

    def render(self, value: OrganisationMembership):
        return mark_safe(  # noqa: S308
            render_to_string(
                "snippets/membership_status_badge.html",
                {"status": value},
            ),
        )


class MemberStatusBadgeColumn(Column):
    """Column that renders member status values."""

    def render(self, value: bool):  # noqa: FBT001
        return mark_safe(  # noqa: S308
            render_to_string(
                "snippets/member_status_badge.html",
                {"is_active": value},
            ),
        )
