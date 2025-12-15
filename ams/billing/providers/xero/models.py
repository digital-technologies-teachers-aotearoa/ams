from django.db.models import CASCADE
from django.db.models import CharField
from django.db.models import Model
from django.db.models import OneToOneField

from ams.billing.models import Account


class XeroContact(Model):
    """Represents a Xero contact linked to a billing account.

    This model stores the mapping between an AMS billing Account and its corresponding
    Xero contact ID, enabling synchronized billing operations between the AMS system
    and the Xero accounting platform.

    Attributes:
        account: One-to-one relationship with the billing Account.
        contact_id: Unique identifier for the contact in Xero's system.
    """

    account = OneToOneField(Account, on_delete=CASCADE, related_name="xero_contact")
    contact_id = CharField(max_length=255, unique=True)

    def __str__(self):
        return f"XeroContact(account={self.account}, contact_id={self.contact_id})"
