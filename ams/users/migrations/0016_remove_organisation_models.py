# Generated migration to remove Organisation and OrganisationMember from users app
# These models have been moved to the organisations app

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_alter_organisationmember_unique_together_and_more'),
        ('organisations', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='organisationmember',
                    name='organisation',
                ),
                migrations.RemoveField(
                    model_name='organisationmember',
                    name='user',
                ),
                migrations.DeleteModel(
                    name='Organisation',
                ),
                migrations.DeleteModel(
                    name='OrganisationMember',
                ),
            ],
            # No database operations - the tables are now managed by the organisations app
            database_operations=[],
        ),
    ]
