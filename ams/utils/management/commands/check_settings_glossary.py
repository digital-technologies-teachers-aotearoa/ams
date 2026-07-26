"""Module for the custom Django check_settings_glossary command."""

import ast
import re
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
        "those settings in its own environment variable table."
    )

    def handle(self, *args, **options):
        """Automatically called when the check_settings_glossary command is given."""
        self.stdout.write(LOG_HEADER.format("📋 Check settings glossary"))

        base_settings_path = Path(settings.BASE_DIR) / "config" / "settings" / "base.py"
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

        code_vars = find_ams_env_vars(base_settings_path.read_text())
        documented_vars = find_documented_vars(glossary_path.read_text())
        deployment_table_vars = find_ams_vars_in_table(deployment_path.read_text())

        undocumented = sorted(code_vars - documented_vars)
        stale = sorted(documented_vars - code_vars)
        duplicated_in_deployment = sorted(code_vars & deployment_table_vars)

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
        if undocumented or stale or duplicated_in_deployment:
            msg = (
                "Settings glossary has drifted from config/settings/base.py "
                "or from deployment.md."
            )
            raise management.base.CommandError(
                msg,
            )

        self.stdout.write(
            f"✅ {len(code_vars)} AMS_* settings match exactly between "
            "base.py and the glossary, with no duplication in deployment.md.\n",
        )
