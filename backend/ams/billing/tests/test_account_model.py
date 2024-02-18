from django.db.utils import IntegrityError
from django.test import TestCase

from ams.test.utils import any_organisation, any_user

from ..models import Account


class AccountModelTests(TestCase):
    def test_account_requires_user_or_organisation(self) -> None:
        Account.objects.create(user=any_user())
        Account.objects.create(organisation=any_organisation())

        with self.assertRaises(IntegrityError):
            Account.objects.create()
