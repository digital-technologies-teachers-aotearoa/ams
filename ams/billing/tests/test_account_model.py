import pytest
from django.db.utils import IntegrityError

from ams.billing.models import Account

pytestmark = pytest.mark.django_db


def test_account_requires_user_or_organisation(user, organisation):
    Account.objects.create(user=user)
    Account.objects.create(organisation=organisation)

    with pytest.raises(IntegrityError):
        Account.objects.create()
