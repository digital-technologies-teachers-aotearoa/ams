import json
import os
import subprocess
import sys

PROBE_SCRIPT = (
    "import json\n"
    "from django.conf import settings\n"
    "from django.core.cache import caches\n"
    "print(json.dumps({\n"
    '    "prefix": settings.CACHES["default"]["KEY_PREFIX"],\n'
    '    "key": caches["default"].make_key("shared-logical-key"),\n'
    "}))\n"
)


def _get_cache_key(environment):
    probe_env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.base",
        "ENVIRONMENT": environment,
        "DATA_STORE_CONNECTION_STRING": "redis://127.0.0.1:6379/0",
    }
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell, no untrusted input
        [sys.executable, "-c", PROBE_SCRIPT],
        env=probe_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_cache_keys_are_isolated_by_environment():
    uat = _get_cache_key("uat")
    production = _get_cache_key("production")

    assert uat["prefix"] == "ams-uat"
    assert production["prefix"] == "ams-production"
    assert uat["key"] != production["key"]
