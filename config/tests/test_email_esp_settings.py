import json
import os
import subprocess
import sys

# Vars config/settings/production.py requires with no default, beyond what the
# ESP selector itself needs. Run in a subprocess so importing the production
# settings module (which mutates the shared base.INSTALLED_APPS list and calls
# sentry_sdk.init() at import time) can't leak into the rest of the test suite.
REQUIRED_PRODUCTION_ENV = {
    "DJANGO_SECRET_KEY": "test-secret-key",
    "DJANGO_ADMIN_URL": "admin/",
    "LOGTAIL_SOURCE_TOKEN": "test-logtail-token",
    "LOGTAIL_INGESTING_HOST": "logs.example.com",
    "SENTRY_DSN": "https://examplepublickey@o0.ingest.sentry.io/0",
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
    "from django.core.mail import get_connection\n"
    # Instantiates the Anymail backend class, exercising its __init__ (which
    # validates required ANYMAIL keys) rather than just reading the settings.
    "get_connection()\n"
    "print(json.dumps({\n"
    '    "EMAIL_BACKEND": settings.EMAIL_BACKEND,\n'
    '    "ANYMAIL_KEYS": sorted(settings.ANYMAIL.keys()),\n'
    "}))\n"
)


def _run_probe(extra_env):
    env = {**os.environ, **REQUIRED_PRODUCTION_ENV}
    env.pop("DJANGO_EMAIL_ESP", None)
    env.update(extra_env)
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
    return subprocess.run(  # noqa: S603 - fixed argv, no shell, no untrusted input
        [sys.executable, "-c", PROBE_SCRIPT],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class TestEmailESPSelector:
    def test_default_is_mailgun(self):
        result = _run_probe(
            {
                "MAILGUN_API_KEY": "test-key",
                "MAILGUN_DOMAIN": "test.mailgun.org",
            },
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["EMAIL_BACKEND"] == "anymail.backends.mailgun.EmailBackend"
        assert payload["ANYMAIL_KEYS"] == sorted(
            ["MAILGUN_API_KEY", "MAILGUN_SENDER_DOMAIN", "MAILGUN_API_URL"],
        )

    def test_postmark_selected(self):
        result = _run_probe(
            {
                "DJANGO_EMAIL_ESP": "postmark",
                "POSTMARK_SERVER_TOKEN": "test-token",
            },
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["EMAIL_BACKEND"] == "anymail.backends.postmark.EmailBackend"
        assert payload["ANYMAIL_KEYS"] == ["POSTMARK_SERVER_TOKEN"]

    def test_mailtrap_selected(self):
        result = _run_probe(
            {
                "DJANGO_EMAIL_ESP": "mailtrap",
                "MAILTRAP_API_TOKEN": "test-token",
            },
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["EMAIL_BACKEND"] == "anymail.backends.mailtrap.EmailBackend"
        assert payload["ANYMAIL_KEYS"] == sorted(
            ["MAILTRAP_API_TOKEN", "MAILTRAP_SANDBOX_ID"],
        )

    def test_invalid_esp_raises(self):
        result = _run_probe({"DJANGO_EMAIL_ESP": "sendgrid"})

        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert "sendgrid" in result.stderr
