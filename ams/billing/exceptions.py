class BillingError(Exception):
    """Base exception for the billing domain."""


class BillingDetailUpdateError(BillingError):
    """Raised when updating user/org billing details fails."""


class BillingInvoiceError(BillingError):
    """Raised when invoice creation fails."""


class SettingNotConfiguredError(BillingError):
    """Raised when a required billing-related setting is missing.

    Args:
        setting_name: Django setting key that is missing/empty.
    """

    def __init__(self, setting_name: str):
        super().__init__(f"Setting '{setting_name}' not configured")
