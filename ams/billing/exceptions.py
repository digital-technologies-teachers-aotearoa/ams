class BillingError(Exception):
    """Base exception for the billing domain."""


class BillingDetailUpdateError(BillingError):
    """Raised when updating user/org billing details fails."""


class BillingInvoiceError(BillingError):
    """Raised when invoice creation fails."""
