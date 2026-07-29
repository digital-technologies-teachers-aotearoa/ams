"""Module for the custom Django check_settings_glossary command."""

import ast
import re
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER

HEADING_PATTERN = re.compile(r"^##\s+`(AMS_[A-Z0-9_]+)`", re.MULTILINE)


def find_ams_env_vars(source: str) -> set[str]:
    """Find every `AMS_*` env var name passed in source."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func
        is_env_call = (isinstance(func, ast.Name) and func.id == "env") or (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "env"
        )
        if not is_env_call:
            continue
        first_arg = node.args[0]
        if (
            isinstance(first_arg, ast.Constant)
            and isinstance(first_arg.value, str)
            and first_arg.value.startswith("AMS_")
        ):
            names.add(first_arg.value)
    return names


def find_documented_vars(source: str) -> set[str]:
    """Find every `AMS_*` name documented as a level-2 heading in the glossary."""
    return set(HEADING_PATTERN.findall(source))


def find_duplicate_headings(source: str) -> set[str]:
    """Find every `AMS_*` level-2 heading that appears more than once."""
    counts = Counter(HEADING_PATTERN.findall(source))
    return {name for name, count in counts.items() if count > 1}


TABLE_ROW_PATTERN = re.compile(r"^\|\s*`(AMS_[A-Z0-9_]+)`\s*\|", re.MULTILINE)


def find_ams_vars_in_table(source: str) -> set[str]:
    """Find every `AMS_*` name used as a leading table-row cell."""
    return set(TABLE_ROW_PATTERN.findall(source))


class Command(management.base.BaseCommand):
    """Required command class for the custom Django check_settings_glossary command."""

    help = (
        "Verify every AMS_* client-decidable setting in config/settings/base.py "
        "has exactly one entry in docs/docs/getting-started/settings-glossary.md, "
        "and vice versa, so the glossary cannot silently drift from the code. "
        "Also verifies docs/docs/hosting/deployment.md doesn't duplicate any of "
        "those settings in its own environment variable table, and that every "
        "AMS_* setting read anywhere in config/settings/ (including "
        "production.py/local.py) is documented in either the glossary or "
        "deployment.md's table."
    )

    def handle(self, *args, **options):
        """Automatically called when the check_settings_glossary command is given."""
        self.stdout.write(LOG_HEADER.format("📋 Check settings glossary"))

        settings_dir = Path(settings.BASE_DIR) / "config" / "settings"
        base_settings_path = settings_dir / "base.py"
        production_settings_path = settings_dir / "production.py"
        local_settings_path = settings_dir / "local.py"
        glossary_path = (
            Path(settings.BASE_DIR)
            / "docs"
            / "docs"
            / "getting-started"
            / "settings-glossary.md"
        )
        deployment_path = (
            Path(settings.BASE_DIR) / "docs" / "docs" / "hosting" / "deployment.md"
        )

        base_vars = find_ams_env_vars(base_settings_path.read_text())
        other_vars = find_ams_env_vars(
            production_settings_path.read_text(),
        ) | find_ams_env_vars(local_settings_path.read_text())
        glossary_source = glossary_path.read_text()
        documented_vars = find_documented_vars(glossary_source)
        duplicate_headings = find_duplicate_headings(glossary_source)
        deployment_table_vars = find_ams_vars_in_table(deployment_path.read_text())

        undocumented = sorted(base_vars - documented_vars)
        stale = sorted(documented_vars - base_vars)
        duplicated_in_deployment = sorted(base_vars & deployment_table_vars)
        undocumented_anywhere = sorted(
            other_vars - documented_vars - deployment_table_vars,
        )

        if undocumented:
            self.stdout.write(
                "❌ In config/settings/base.py but missing from the glossary: "
                + ", ".join(undocumented),
            )
        if stale:
            self.stdout.write(
                "❌ In the glossary but not read from config/settings/base.py: "
                + ", ".join(stale),
            )
        if duplicated_in_deployment:
            self.stdout.write(
                "❌ Documented in the settings glossary but also duplicated in "
                "deployment.md's environment variable table (should only live in "
                "the glossary): " + ", ".join(duplicated_in_deployment),
            )
        if undocumented_anywhere:
            self.stdout.write(
                "❌ Read in config/settings/production.py or local.py but "
                "documented in neither the glossary nor deployment.md's "
                "environment variable table: " + ", ".join(undocumented_anywhere),
            )
        if duplicate_headings:
            self.stdout.write(
                "❌ Documented under more than one `##` heading in the glossary: "
                + ", ".join(sorted(duplicate_headings)),
            )
        if (
            undocumented
            or stale
            or duplicated_in_deployment
            or undocumented_anywhere
            or duplicate_headings
        ):
            msg = (
                "Settings glossary has drifted from config/settings/base.py "
                "or from deployment.md."
            )
            raise management.base.CommandError(
                msg,
            )

        self.stdout.write(
            f"✅ {len(base_vars)} AMS_* settings match exactly between "
            "base.py and the glossary, with no duplication in deployment.md, "
            f"and {len(other_vars)} AMS_* settings read from production.py/"
            "local.py are documented in the glossary or deployment.md.\n",
        )
