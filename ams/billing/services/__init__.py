"""Service layer for billing domain.

Provides structured modules:
 - base: abstract BillingService + get_billing_service
 - membership: membership-related billing orchestration
 - (future) invoice: helpers for invoice creation/email

Legacy imports:
Code previously lived in ams.billing.service; that module now re-exports
symbols with a deprecation warning.
"""

from .base import BillingService  # noqa: F401
from .base import get_billing_service  # noqa: F401
