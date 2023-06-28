from typing import Any

from django.db import migrations


def add_maori_locale(apps: Any, schema_editor: Any) -> None:
    Locale = apps.get_model("wagtailcore.Locale")
    Locale.objects.create(language_code="mi")


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailcore", "0083_workflowcontenttype"),
        ("dtta", "0001_update_homepage"),
    ]

    operations = [
        migrations.RunPython(add_maori_locale),
    ]
