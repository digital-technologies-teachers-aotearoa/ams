"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="EVKoOpeZaj0UU2PUgwoXmGDwYvlpOUqL2IT3dK5LXfsgqacuqeaLoSoPWCrzIYgr",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/test-media/"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {
            "location": "tmp/public-media/",
            "base_url": "/public-media/",
        },
    },
    "private": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {
            "location": "tmp/private-media/",
            "base_url": "/private-media/",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Billing
# ------------------------------------------------------------------------------
BILLING_SERVICE_CLASS = "ams.billing.providers.xero.MockXeroBillingService"
BILLING_EMAIL_WHITELIST_REGEX = None
XERO_CLIENT_ID = "test-client-id"
XERO_CLIENT_SECRET = "test-client-secret"  # noqa: S105
XERO_TENANT_ID = "test-tenant-id"
XERO_WEBHOOK_KEY = "test-webhook-key"
XERO_ACCOUNT_CODE = "200"
XERO_AMOUNT_TYPE = "INCLUSIVE"
XERO_CURRENCY_CODE = "NZD"
XERO_EMAIL_INVOICES = True
