from datetime import timedelta

import pytest
from django.utils import timezone

from ams.memberships.forms import CreateIndividualMembershipForm
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOptionType

from .factories import MembershipOptionFactory
from .factories import UserFactory

pytestmark = pytest.mark.django_db


def test_start_date_overlap_validation():
    user = UserFactory()
    option = MembershipOptionFactory(type=MembershipOptionType.INDIVIDUAL)
    today = timezone.localdate()
    # Existing active membership
    IndividualMembership.objects.create(
        user=user,
        membership_option=option,
        start_date=today,
        expiry_date=today + timedelta(days=30),
        created_datetime=timezone.now(),
    )
    # Try to create a new membership that starts during the existing one
    form = CreateIndividualMembershipForm(
        data={
            "membership_option": option.id,
            "start_date": today + timedelta(days=1),
        },
        user=user,
    )
    assert not form.is_valid()  # Triggers clean and should fail
    assert "start_date" in form.errors
    assert (
        "already have a non-cancelled membership active" in form.errors["start_date"][0]
    )


def test_start_date_no_overlap():
    user = UserFactory()
    option = MembershipOptionFactory(type=MembershipOptionType.INDIVIDUAL)
    today = timezone.localdate()
    IndividualMembership.objects.create(
        user=user,
        membership_option=option,
        start_date=today,
        expiry_date=today + timedelta(days=30),
        created_datetime=timezone.now(),
    )
    # New membership starts after the previous one ends
    form = CreateIndividualMembershipForm(
        data={
            "membership_option": option.id,
            "start_date": today + timedelta(days=31),
        },
        user=user,
    )
    assert form.is_valid()
    # Should not raise
    form.save(user=user)
