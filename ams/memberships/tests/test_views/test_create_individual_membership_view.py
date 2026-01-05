from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.users.tests.factories import UserFactory

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
        reverse("memberships:apply-individual"),
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
    assert not membership.invoices.exists()
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
        reverse("memberships:apply-individual"),
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
