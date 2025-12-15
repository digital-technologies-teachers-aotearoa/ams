"""Tests for Xero models."""

import pytest
from django.db.utils import IntegrityError

from ams.billing.models import Account
from ams.billing.providers.xero.models import XeroContact

pytestmark = pytest.mark.django_db


class TestXeroContact:
    """Tests for XeroContact model."""

    def test_create_xero_contact_for_user_account(self, account_user):
        """Test creating XeroContact linked to user account."""
        xero_contact = XeroContact.objects.create(
            account=account_user,
            contact_id="test-contact-id-123",
        )
        assert xero_contact.account == account_user
        assert xero_contact.contact_id == "test-contact-id-123"
        assert (
            str(xero_contact)
            == f"XeroContact(account={account_user}, contact_id=test-contact-id-123)"
        )

    def test_create_xero_contact_for_organisation_account(self, account_organisation):
        """Test creating XeroContact linked to organisation account."""
        xero_contact = XeroContact.objects.create(
            account=account_organisation,
            contact_id="test-contact-id-456",
        )
        assert xero_contact.account == account_organisation
        assert xero_contact.contact_id == "test-contact-id-456"

    def test_xero_contact_has_one_to_one_relationship(self, account_user):
        """Test that XeroContact has one-to-one relationship with Account."""
        xero_contact = XeroContact.objects.create(
            account=account_user,
            contact_id="test-contact-id-789",
        )
        # Access through reverse relation
        assert account_user.xero_contact == xero_contact

    def test_xero_contact_contact_id_must_be_unique(
        self,
        account_user,
        account_organisation,
    ):
        """Test that contact_id must be unique."""
        XeroContact.objects.create(
            account=account_user,
            contact_id="duplicate-contact-id",
        )
        # Attempting to create another XeroContact with same contact_id should fail
        with pytest.raises(IntegrityError):
            XeroContact.objects.create(
                account=account_organisation,
                contact_id="duplicate-contact-id",
            )

    def test_deleting_account_deletes_xero_contact(self, account_user):
        """Test cascade deletion when account is deleted."""
        XeroContact.objects.create(
            account=account_user,
            contact_id="test-contact-cascade",
        )
        account_id = account_user.id
        account_user.delete()

        # XeroContact should be deleted
        assert not XeroContact.objects.filter(
            contact_id="test-contact-cascade",
        ).exists()
        assert not Account.objects.filter(id=account_id).exists()
