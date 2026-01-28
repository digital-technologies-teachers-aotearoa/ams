import logging

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from config.settings.base import *  # noqa: F403
from config.settings.base import DATABASES
from config.settings.base import INSTALLED_APPS
from config.settings.base import Q_CLUSTER
from config.settings.base import env

# GENERAL
# ------------------------------------------------------------------------------
DEPLOYED = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["dtta.org.nz"])

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)
# Add connection timeout to prevent hung connections
DATABASES["default"]["OPTIONS"] = {
    "connect_timeout": 10,
    "options": "-c statement_timeout=30000",  # 30 second query timeout
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-name
SESSION_COOKIE_NAME = "__Secure-sessionid"
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-name
CSRF_COOKIE_NAME = "__Secure-csrftoken"
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
# Could upgrade in future to dedicated cache server
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="Association Management Software <noreply@ams.com>",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX",
    default="[Association Management Software] ",
)
ACCOUNT_EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Anymail
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
INSTALLED_APPS += ["anymail"]
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
# https://anymail.readthedocs.io/en/stable/esps/mailgun/
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_DOMAIN"),
    "MAILGUN_API_URL": env("MAILGUN_API_URL", default="https://api.mailgun.net/v3"),
}

# Django-Q2 - Production settings
# ------------------------------------------------------------------------------
Q_CLUSTER["workers"] = 1
Q_CLUSTER["poll"] = 1
Q_CLUSTER["save_limit"] = 5000  # Keep more history in production


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGTAIL_SOURCE_TOKEN = env("LOGTAIL_SOURCE_TOKEN")
LOGTAIL_INGESTING_HOST = env("LOGTAIL_INGESTING_HOST")
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"  # noqa: F405
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # Human-readable logs for Digital Ocean console
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
        # Structured logs for Logtail
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        # DigitalOcean captures stdout/stderr automatically
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "verbose",
        },
        # Better Stack Logtail
        "logtail": {
            "class": "logtail.LogtailHandler",
            "level": LOG_LEVEL,
            "formatter": "json",
            "source_token": LOGTAIL_SOURCE_TOKEN,
            "host": f"https://{LOGTAIL_INGESTING_HOST}",
        },
    },
    # Root logger: everything flows through here
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console", "logtail"],
    },
    "loggers": {
        # Django 500 errors
        "django.request": {
            "level": "ERROR",
            "propagate": True,
        },
        # Avoid SQL noise in prod
        "django.db.backends": {
            "level": "ERROR",
            "propagate": False,
        },
        # DisallowedHost spam protection
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "propagate": False,
        },
        # Prevent Sentry SDK from logging about itself
        "sentry_sdk": {
            "level": "ERROR",
            "propagate": False,
        },
        # Gunicorn logger integration
        "gunicorn.error": {
            "level": "INFO",
            "propagate": True,
        },
        # Set to WARNING if log volume too high
        "gunicorn.access": {
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Better Stack (uses Sentry SDK)
# ------------------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN")
SENTRY_LOG_LEVEL = env.int("SENTRY_LOG_LEVEL", logging.INFO)
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT", default="production")
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0)

sentry_logging = LoggingIntegration(
    level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)
integrations = [sentry_logging, DjangoIntegration()]
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=integrations,
    environment=SENTRY_ENVIRONMENT,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
)


# Discourse SSO
# ------------------------------------------------------------------------------
DISCOURSE_REDIRECT_DOMAIN = env("DISCOURSE_REDIRECT_DOMAIN", default=None)
DISCOURSE_CONNECT_SECRET = env("DISCOURSE_CONNECT_SECRET", default=None)

# Billing
# ------------------------------------------------------------------------------
BILLING_SERVICE_CLASS = env(
    "AMS_BILLING_SERVICE_CLASS",
    default="ams.billing.providers.xero.XeroBillingService",
)
BILLING_EMAIL_WHITELIST_REGEX = env("AMS_BILLING_EMAIL_WHITELIST_REGEX", default=None)

# Xero Billing Settings
# ------------------------------------------------------------------------------
XERO_CLIENT_ID = env("XERO_CLIENT_ID")
XERO_CLIENT_SECRET = env("XERO_CLIENT_SECRET")
XERO_TENANT_ID = env("XERO_TENANT_ID")
XERO_WEBHOOK_KEY = env("XERO_WEBHOOK_KEY")
XERO_ACCOUNT_CODE = env("XERO_ACCOUNT_CODE")
XERO_AMOUNT_TYPE = env("XERO_AMOUNT_TYPE")
XERO_CURRENCY_CODE = env("XERO_CURRENCY_CODE")
