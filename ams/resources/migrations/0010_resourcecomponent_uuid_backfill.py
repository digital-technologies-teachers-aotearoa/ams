import uuid

from django.db import migrations


def assign_unique_uuids(apps, schema_editor):
    ResourceComponent = apps.get_model("resources", "ResourceComponent")
    for component in ResourceComponent.objects.all():
        component.uuid = uuid.uuid4()
        component.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0009_resourcecomponent_uuid"),
    ]

    operations = [
        migrations.RunPython(assign_unique_uuids, migrations.RunPython.noop),
    ]
