# Generated migration to move Organisation and OrganisationMember from users to organisations app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    # Use SeparateDatabaseAndState to create Django models without changing the database
    # This allows us to "claim" the existing tables from the users app
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Organisation',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                        ('name', models.CharField(max_length=255)),
                        ('telephone', models.CharField(max_length=255)),
                        ('email', models.CharField(max_length=255)),
                        ('contact_name', models.CharField(max_length=255)),
                        ('postal_address', models.CharField(max_length=255)),
                        ('postal_suburb', models.CharField(blank=True, max_length=255)),
                        ('postal_city', models.CharField(max_length=255)),
                        ('postal_code', models.CharField(max_length=255)),
                        ('street_address', models.CharField(blank=True, max_length=255)),
                        ('suburb', models.CharField(blank=True, max_length=255)),
                        ('city', models.CharField(blank=True, max_length=255)),
                    ],
                    options={
                        'db_table': 'users_organisation',
                    },
                ),
                migrations.CreateModel(
                    name='OrganisationMember',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                        ('invite_email', models.CharField(blank=True, max_length=255)),
                        ('invite_token', models.UUIDField(default=uuid.uuid4, editable=False)),
                        ('created_datetime', models.DateTimeField()),
                        ('accepted_datetime', models.DateTimeField(null=True)),
                        ('declined_datetime', models.DateTimeField(null=True)),
                        ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('MEMBER', 'Member')], default='MEMBER', help_text='Member role within the organisation', max_length=10)),
                        ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organisation_members', to='organisations.organisation')),
                        ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='organisation_members', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'users_organisationmember',
                    },
                ),
                migrations.AddConstraint(
                    model_name='organisationmember',
                    constraint=models.UniqueConstraint(condition=models.Q(('declined_datetime__isnull', True)), fields=('user', 'organisation'), name='unique_active_org_member'),
                ),
            ],
            # No database operations - the tables already exist from the users app
            database_operations=[],
        ),
    ]
