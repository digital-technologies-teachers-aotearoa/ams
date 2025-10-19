from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOptionType
from ams.users.tests.factories import UserFactory

from .factories import MembershipOptionFactory

pytestmark = pytest.mark.django_db


def test_get_application_form(client):
    user = UserFactory()
    MembershipOptionFactory(type=MembershipOptionType.INDIVIDUAL)
    client.force_login(user)

    resp = client.get(reverse("memberships:apply"))
    assert resp.status_code == HTTPStatus.OK
    assert b"Apply for Membership" in resp.content
    # Start date should be present
    assert b"membership-start-date" in resp.content
    # JSON script id for option end dates mapping
    assert b"option-end-dates-data" in resp.content


def test_post_application_creates_membership(client):
    user = UserFactory()
    option = MembershipOptionFactory(type=MembershipOptionType.INDIVIDUAL)
    client.force_login(user)

    resp = client.post(
        reverse("memberships:apply"),
        data={
            "membership_option": option.id,
        },
        follow=True,
    )
    assert resp.status_code == HTTPStatus.OK
    membership = IndividualMembership.objects.get(user=user, membership_option=option)
    assert membership.start_date == timezone.localdate()
    assert membership.approved_datetime is None


def test_user_cannot_set_user_field(client):
    user1 = UserFactory()
    user2 = UserFactory()
    option = MembershipOptionFactory(type=MembershipOptionType.INDIVIDUAL)
    client.force_login(user1)

    # Attempt to spoof by submitting extra field (ignored by form)
    resp = client.post(
        reverse("memberships:apply"),
        data={
            "membership_option": option.id,
            "user": user2.id,
        },
    )
    assert resp.status_code in (302, 200)
    assert IndividualMembership.objects.filter(user=user2).count() == 0
    assert IndividualMembership.objects.filter(user=user1).count() == 1
