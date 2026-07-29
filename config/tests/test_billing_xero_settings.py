import json
import os
import subprocess
import sys

# Vars config/settings/production.py requires with no default, beyond what the
# billing service class selector itself needs. Run in a subprocess so importing
# the production settings module (which mutates the shared base.INSTALLED_APPS
# list and calls sentry_sdk.init() at import time) can't leak into the rest of
# the test suite.
REQUIRED_PRODUCTION_ENV = {
    "DJANGO_SECRET_KEY": "test-secret-key",
    "DJANGO_ADMIN_URL": "admin/",
    "LOGTAIL_SOURCE_TOKEN": "test-logtail-token",
    "LOGTAIL_INGESTING_HOST": "logs.example.com",
    "SENTRY_DSN": "https://examplepublickey@o0.ingest.sentry.io/0",
    "MAILGUN_API_KEY": "test-key",
    "MAILGUN_DOMAIN": "test.mailgun.org",
}

XERO_ENV_VARS = (
    "XERO_CLIENT_ID",
    "XERO_CLIENT_SECRET",
    "XERO_TENANT_ID",
    "XERO_WEBHOOK_KEY",
    "XERO_ACCOUNT_CODE",
    "XERO_AMOUNT_TYPE",
    "XERO_CURRENCY_CODE",
)

FULL_XERO_ENV = {
    "XERO_CLIENT_ID": "test-client-id",
    "XERO_CLIENT_SECRET": "test-client-secret",
    "XERO_TENANT_ID": "test-tenant-id",
    "XERO_WEBHOOK_KEY": "test-webhook-key",
    "XERO_ACCOUNT_CODE": "200",
    "XERO_AMOUNT_TYPE": "INCLUSIVE",
    "XERO_CURRENCY_CODE": "NZD",
}

PROBE_SCRIPT = (
    "import json\n"
    "from django.conf import settings\n"
    "print(json.dumps({\n"
    # Every XERO_* name is always defined (never unset) so that the
    # unconditionally-wired webhook view (ams/billing/urls.py) never hits an
    # AttributeError — the gate controls whether it's a real value or None.
    '    "HAS_XERO_SETTINGS": settings.XERO_CLIENT_ID is not None,\n'
    '    "BILLING_SERVICE_CLASS": settings.BILLING_SERVICE_CLASS,\n'
    "}))\n"
)


def _run_probe(extra_env):
    env = {**os.environ, **REQUIRED_PRODUCTION_ENV}
    env.pop("AMS_BILLING_SERVICE_CLASS", None)
    for key in XERO_ENV_VARS:
        env.pop(key, None)
    env.update(extra_env)
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
    return subprocess.run(  # noqa: S603 - fixed argv, no shell, no untrusted input
        [sys.executable, "-c", PROBE_SCRIPT],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class TestBillingXeroSettingsGating:
    def test_default_is_xero_and_requires_xero_settings(self):
        result = _run_probe({})

        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr

    def test_xero_service_class_requires_xero_settings(self):
        result = _run_probe(
            {
                "AMS_BILLING_SERVICE_CLASS": (
                    "ams.billing.providers.xero.XeroBillingService"
                ),
            },
        )

        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr

    def test_mock_xero_service_class_requires_xero_settings(self):
        result = _run_probe(
            {
                "AMS_BILLING_SERVICE_CLASS": (
                    "ams.billing.providers.xero.MockXeroBillingService"
                ),
            },
        )

        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr

    def test_xero_service_class_succeeds_when_xero_settings_present(self):
        result = _run_probe(
            {
                "AMS_BILLING_SERVICE_CLASS": (
                    "ams.billing.providers.xero.XeroBillingService"
                ),
                **FULL_XERO_ENV,
            },
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["HAS_XERO_SETTINGS"] is True

    def test_non_xero_service_class_does_not_require_xero_settings(self):
        result = _run_probe(
            {
                "AMS_BILLING_SERVICE_CLASS": (
                    "ams.billing.providers.mock.MockBillingService"
                ),
            },
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert (
            payload["BILLING_SERVICE_CLASS"]
            == "ams.billing.providers.mock.MockBillingService"
        )
        assert payload["HAS_XERO_SETTINGS"] is False

    def test_unrecognised_service_class_does_not_require_xero_settings(self):
        # AMS_BILLING_SERVICE_CLASS is a dotted import path, validated lazily by
        # import_string() only when the service is actually used
        # (ams.billing.services.base.get_billing_service()) — not eagerly here.
        # A value that isn't one of the two known Xero-backed classes is
        # therefore treated as non-Xero, unlike DJANGO_EMAIL_ESP's small fixed
        # enum which raises ImproperlyConfigured on an unrecognised value.
        result = _run_probe({"AMS_BILLING_SERVICE_CLASS": "not.a.real.Service"})

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["HAS_XERO_SETTINGS"] is False
