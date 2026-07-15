from django.db import migrations
from django.db import models


def backfill_english_translations(apps, schema_editor):
    Term = apps.get_model("terms", "Term")
    TermVersion = apps.get_model("terms", "TermVersion")

    Term.objects.filter(
        models.Q(name_en__isnull=True) | models.Q(name_en=""),
    ).update(name_en=models.F("name"))

    TermVersion.objects.filter(
        models.Q(content_en__isnull=True) | models.Q(content_en=""),
    ).update(content_en=models.F("content"))


class Migration(migrations.Migration):

    dependencies = [
        ("terms", "0002_term_name_en_term_name_mi_termversion_content_en_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_english_translations, migrations.RunPython.noop),
    ]
