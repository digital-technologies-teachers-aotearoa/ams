import pytest
from django.test import override_settings
from django.utils import timezone

from ams.memberships.forms import CreateIndividualMembershipForm
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_zero_cost_membership_form_save_directly():
    """Test direct form save for zero-cost membership."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)
    assert form.is_valid()

    membership = form.save(user=user)

    assert membership.approved_datetime is not None
    assert not membership.invoices.exists()
    assert membership.status().name == "ACTIVE"


def test_paid_membership_form_save_directly():
    """Test direct form save for paid membership."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=49.99,
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)
    assert form.is_valid()

    membership = form.save(user=user)

    assert membership.approved_datetime is None
    # Note: No invoice in test environment since billing service is not configured
    assert membership.status().name == "PENDING"


def test_zero_cost_membership_shows_active_immediately():
    """Test that zero-cost membership shows as having active membership."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
        name="Free Individual Membership",
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)
    assert form.is_valid()

    membership = form.save(user=user)

    # Membership should be automatically approved
    assert membership.approved_datetime is not None
    assert membership.status().name == "ACTIVE"
    assert not membership.invoices.exists()

    # User should now have an active membership
    assert user.individual_memberships.filter(
        approved_datetime__isnull=False,
        cancelled_datetime__isnull=True,
    ).exists()


def test_archived_membership_option_not_available():
    """Test that archived membership options cannot be selected."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
        archived=True,
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)

    assert not form.is_valid()
    assert "membership_option" in form.errors


def test_archived_membership_option_not_in_queryset():
    """Test that archived membership options are excluded from form queryset."""
    user = UserFactory()
    active_option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
        archived=False,
    )
    archived_option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
        archived=True,
    )

    form = CreateIndividualMembershipForm(user=user)

    option_ids = [opt.id for opt in form.fields["membership_option"].queryset]
    assert active_option.id in option_ids
    assert archived_option.id not in option_ids


@override_settings(REQUIRE_FREE_MEMBERSHIP_APPROVAL=True)
def test_free_membership_requires_approval_when_enabled():
    """Test that free memberships require approval when feature is enabled."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)
    assert form.is_valid()

    membership = form.save(user=user)

    # Should NOT be auto-approved
    assert membership.approved_datetime is None
    assert membership.status().name == "PENDING"
    assert not membership.invoices.exists()


@override_settings(REQUIRE_FREE_MEMBERSHIP_APPROVAL=False)
def test_free_membership_auto_approved_when_disabled():
    """Test that free memberships are auto-approved when feature is disabled."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)
    assert form.is_valid()

    membership = form.save(user=user)

    # Should be auto-approved (default behavior)
    assert membership.approved_datetime is not None
    assert membership.status().name == "ACTIVE"
    assert not membership.invoices.exists()


@override_settings(REQUIRE_FREE_MEMBERSHIP_APPROVAL=True)
def test_paid_membership_unchanged_when_approval_required():
    """Test that paid memberships are unaffected by approval setting."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=49.99,
    )

    form_data = {
        "membership_option": option.id,
        "start_date": timezone.localdate(),
    }
    form = CreateIndividualMembershipForm(data=form_data, user=user)
    assert form.is_valid()

    membership = form.save(user=user)

    # Paid memberships should still not be auto-approved (pending payment)
    assert membership.approved_datetime is None
    assert membership.status().name == "PENDING"
