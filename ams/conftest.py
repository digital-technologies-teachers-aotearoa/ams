from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from ams.billing.tests.factories import AccountFactory
from ams.billing.tests.factories import InvoiceFactory
from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.users.models import User
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory


def pytest_configure():
    # Ensure the staticfiles directory exists
    Path("staticfiles/").mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def organisation(db):
    return OrganisationFactory()


@pytest.fixture
def organisation_member(db, user, organisation):
    return OrganisationMemberFactory(user=user, organisation=organisation)


@pytest.fixture
def membership_option_individual(db):
    return MembershipOptionFactory(type="INDIVIDUAL")


@pytest.fixture
def membership_option_organisation(db):
    return MembershipOptionFactory(type="ORGANISATION")


@pytest.fixture
def individual_membership(db, user, membership_option_individual):
    return IndividualMembershipFactory(
        user=user,
        membership_option=membership_option_individual,
    )


@pytest.fixture
def individual_membership_pending(db, user, membership_option_individual):
    """Individual membership not yet approved (approved_datetime=None)."""
    return IndividualMembershipFactory(
        user=user,
        membership_option=membership_option_individual,
        pending=True,
    )


@pytest.fixture
def individual_membership_cancelled(db, user, membership_option_individual):
    """Cancelled individual membership."""
    return IndividualMembershipFactory(
        user=user,
        membership_option=membership_option_individual,
        cancelled=True,
    )


@pytest.fixture
def organisation_membership(db, organisation, membership_option_organisation):
    return OrganisationMembershipFactory(
        organisation=organisation,
        membership_option=membership_option_organisation,
    )


@pytest.fixture
def organisation_membership_active(db, organisation, membership_option_organisation):
    """Active organisation membership (alias of default)."""
    return OrganisationMembershipFactory(
        organisation=organisation,
        membership_option=membership_option_organisation,
        active=True,
    )


@pytest.fixture
def account_user(db, user):
    return AccountFactory(user_account=True, user=user)


@pytest.fixture
def account_organisation(db, organisation):
    return AccountFactory(organisation_account=True, organisation=organisation)


@pytest.fixture
def invoice_for_individual(db, account_user):
    """Invoice linked to a user account (individual)."""
    return InvoiceFactory(account=account_user)


@pytest.fixture
def invoice_for_organisation(db, account_organisation):
    """Invoice linked to an organisation account."""
    return InvoiceFactory(account=account_organisation)


@pytest.fixture
def invoice_user(db, account_user):
    return InvoiceFactory(account=account_user)


@pytest.fixture
def invoice_organisation(db, account_organisation):
    return InvoiceFactory(account=account_organisation)


@pytest.fixture
def admin_user(db):
    user_model = get_user_model()
    password = f"admin-{get_random_string(12)}!"
    return user_model.objects.create_user(
        email="admin@example.com",
        password=password,
        is_staff=True,
        is_superuser=True,
    )
