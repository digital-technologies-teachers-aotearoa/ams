"""Tests for user tables."""

from datetime import timedelta

import pytest
from django.utils import timezone

from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.users.tables import MembershipTable

pytestmark = pytest.mark.django_db


class TestMembershipTableActionsColumn:
    """Tests for the actions column on MembershipTable."""

    def test_actions_column_exists(self):
        """Test that actions column is configured on the table."""
        membership = IndividualMembershipFactory(
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.INDIVIDUAL,
        )

        table = MembershipTable([membership])

        assert "actions" in table.base_columns

    def test_actions_column_renders_cancel_button_for_active_membership(self):
        """Test that actions column renders cancel button for active membership."""
        membership = IndividualMembershipFactory(
            active=True,
            membership_option__type=MembershipOptionType.INDIVIDUAL,
        )

        table = MembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" in html

    def test_actions_column_renders_cancel_button_for_pending_membership(self):
        """Test that actions column renders cancel button for pending membership."""
        membership = IndividualMembershipFactory(
            pending=True,
            membership_option__type=MembershipOptionType.INDIVIDUAL,
        )

        table = MembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" in html

    def test_actions_column_no_cancel_button_for_cancelled_membership(self):
        """Test that actions column does not render cancel button for cancelled
        membership."""
        membership = IndividualMembershipFactory(
            cancelled=True,
            membership_option__type=MembershipOptionType.INDIVIDUAL,
        )

        table = MembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" not in html

    def test_actions_column_no_cancel_button_for_expired_membership(self):
        """Test that actions column does not render cancel button for expired
        membership."""
        membership = IndividualMembershipFactory(
            expired=True,
            membership_option__type=MembershipOptionType.INDIVIDUAL,
        )

        table = MembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" not in html
