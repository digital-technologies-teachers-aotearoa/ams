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


class XeroMutex(Model):
    """Database-level mutex for coordinating Xero API access.

    This model is used to implement an exclusive lock mechanism via database
    table locking (LOCK billing_xeromutex). Only one instance can interact
    with the Xero API at a time, preventing concurrent requests that could
    exceed Xero's API rate limits.

    The model itself has no fields; it exists solely for table-level locking.
    See: https://developer.xero.com/documentation/guides/oauth2/limits/#api-rate-limits
    """

    def __str__(self):
        return "Xero Mutex (Exclusive Lock)"
