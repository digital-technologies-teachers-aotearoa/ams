"""Add seats field and populate from max_seats for existing rows.

Generated migration: adds nullable `seats`, copies values from `max_seats`,
then sets `seats` to non-nullable.
"""
from django.db import migrations, models


def copy_max_seats_to_seats(apps, schema_editor):
    OrganisationMembership = apps.get_model("memberships", "OrganisationMembership")
    # Copy max_seats into seats for existing rows where seats is null
    for om in OrganisationMembership.objects.all():
        if om.seats is None:
            om.seats = om.max_seats or 0
            om.save(update_fields=["seats"])


class Migration(migrations.Migration):

    dependencies = [
        ("memberships", "0008_organisationmembership_max_seats"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisationmembership",
            name="seats",
            field=models.DecimalField(decimal_places=0, max_digits=10, null=True),
        ),
        migrations.RunPython(copy_max_seats_to_seats, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='organisationmembership',
            name='seats',
            field=models.DecimalField(decimal_places=0, help_text="Number of seats allocated to this membership. Cannot exceed the membership option's max_seats limit if set.", max_digits=10),
        ),
    ]
