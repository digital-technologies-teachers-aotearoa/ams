"""Tests for the check_settings_glossary management command."""

import pytest
from django.core import management
from django.core.management.base import CommandError
from django.test import override_settings

from ams.utils.management.commands.check_settings_glossary import find_ams_env_vars
from ams.utils.management.commands.check_settings_glossary import (
    find_duplicate_headings,
)


def test_find_ams_env_vars_finds_ams_prefixed_calls():
    source = (
        'FOO = env("AMS_FOO", default="bar")\n'
        'BAR = env("NOT_AMS", default="baz")\n'
        'BAZ = env.bool("AMS_BAZ", default=False)\n'
    )
    assert find_ams_env_vars(source) == {"AMS_FOO", "AMS_BAZ"}


def test_find_duplicate_headings_detects_repeated_heading():
    source = (
        "## `AMS_FOO`\n\nSome text.\n\n"
        "## `AMS_BAR`\n\nMore text.\n\n"
        "## `AMS_FOO`\n\nDuplicated section.\n"
    )
    assert find_duplicate_headings(source) == {"AMS_FOO"}


def test_find_duplicate_headings_empty_when_no_repeats():
    source = "## `AMS_FOO`\n\n## `AMS_BAR`\n"
    assert find_duplicate_headings(source) == set()


def _write_fake_project(
    base_dir,
    *,
    production_source="",
    local_source="",
    glossary_source="",
    deployment_source="",
):
    settings_dir = base_dir / "config" / "settings"
    settings_dir.mkdir(parents=True)
    (settings_dir / "base.py").write_text('FOO = env("AMS_FOO", default="bar")\n')
    (settings_dir / "production.py").write_text(production_source)
    (settings_dir / "local.py").write_text(local_source)

    docs_dir = base_dir / "docs" / "docs" / "getting-started"
    docs_dir.mkdir(parents=True)
    (docs_dir / "settings-glossary.md").write_text(
        "## `AMS_FOO`\n\nSome text.\n\n" + glossary_source,
    )

    hosting_dir = base_dir / "docs" / "docs" / "hosting"
    hosting_dir.mkdir(parents=True)
    (hosting_dir / "deployment.md").write_text(deployment_source)


def test_command_fails_on_undocumented_production_or_local_var(tmp_path, capsys):
    _write_fake_project(
        tmp_path,
        production_source='BAR = env("AMS_BAR", default=None)\n',
    )

    with override_settings(BASE_DIR=tmp_path), pytest.raises(CommandError):
        management.call_command("check_settings_glossary")

    assert "AMS_BAR" in capsys.readouterr().out


def test_command_passes_when_production_var_documented_in_deployment_table(tmp_path):
    _write_fake_project(
        tmp_path,
        production_source='BAR = env("AMS_BAR", default=None)\n',
        deployment_source="| `AMS_BAR` | Optional | example | Some description |\n",
    )

    with override_settings(BASE_DIR=tmp_path):
        management.call_command("check_settings_glossary")


def test_command_still_fails_on_production_var_documented_only_in_glossary(
    tmp_path,
    capsys,
):
    """Documenting a production/local-only var via a glossary heading (rather
    than deployment.md's table) must still fail -- T39's binding decision on
    AMS_BILLING_SERVICE_CLASS/AMS_BILLING_EMAIL_WHITELIST_REGEX is "do not
    add them to the settings glossary", not "either location is fine"."""
    _write_fake_project(
        tmp_path,
        production_source='BAR = env("AMS_BAR", default=None)\n',
        glossary_source="## `AMS_BAR`\n\nSome text.\n",
    )

    with override_settings(BASE_DIR=tmp_path), pytest.raises(CommandError):
        management.call_command("check_settings_glossary")

    assert "AMS_BAR" in capsys.readouterr().out


def test_command_fails_on_duplicated_glossary_heading(tmp_path):
    _write_fake_project(
        tmp_path,
        glossary_source="## `AMS_FOO`\n\nDuplicated section.\n",
    )

    with override_settings(BASE_DIR=tmp_path), pytest.raises(CommandError):
        management.call_command("check_settings_glossary")


def test_command_passes_against_current_repo_state():
    """AMS_BILLING_SERVICE_CLASS / AMS_BILLING_EMAIL_WHITELIST_REGEX are read
    in production.py/local.py (not base.py) and documented in
    deployment.md's table, not the glossary -- confirm the widened check
    recognises that as documented, not missing."""
    management.call_command("check_settings_glossary")
