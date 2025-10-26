"""Tests for zero-cost membership automatic approval."""

from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.forms import CreateIndividualMembershipForm
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOptionType
from ams.users.tests.factories import UserFactory

from .factories import MembershipOptionFactory

pytestmark = pytest.mark.django_db


def test_zero_cost_membership_auto_approved(client):
    """Test that zero-cost memberships are automatically approved."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=0,
    )
    client.force_login(user)

    resp = client.post(
        reverse("memberships:apply"),
        data={
            "membership_option": option.id,
            "start_date": timezone.localdate(),
        },
        follow=True,
    )

    assert resp.status_code == HTTPStatus.OK
    membership = IndividualMembership.objects.get(user=user, membership_option=option)
    assert membership.start_date == timezone.localdate()
    assert membership.approved_datetime is not None
    assert membership.invoice is None
    assert membership.status().name == "ACTIVE"


def test_paid_membership_not_auto_approved(client):
    """Test that paid memberships are not automatically approved."""
    user = UserFactory()
    option = MembershipOptionFactory(
        type=MembershipOptionType.INDIVIDUAL,
        cost=99.99,
    )
    client.force_login(user)

    resp = client.post(
        reverse("memberships:apply"),
        data={
            "membership_option": option.id,
            "start_date": timezone.localdate(),
        },
        follow=True,
    )

    assert resp.status_code == HTTPStatus.OK
    membership = IndividualMembership.objects.get(user=user, membership_option=option)
    assert membership.start_date == timezone.localdate()
    assert membership.approved_datetime is None
    # Note: No invoice in test environment since billing service is not configured
    assert membership.status().name == "PENDING"


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
    assert membership.invoice is None
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
    assert membership.invoice is None

    # User should now have an active membership
    assert user.individual_memberships.filter(
        approved_datetime__isnull=False,
        cancelled_datetime__isnull=True,
    ).exists()
