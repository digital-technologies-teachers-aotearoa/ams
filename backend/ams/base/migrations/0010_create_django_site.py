# -*- coding: utf-8 -*-
from os import environ
from typing import Any

from django.contrib.sites.models import Site
from django.db import migrations


def create_django_site(apps: Any, schema_editor: Any) -> None:
    Site.objects.create(name=environ["APPLICATION_SITE_NAME"], domain=environ["APPLICATION_WEB_HOST"])


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0009_remove_footer_site_logo_url_and_more"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(create_django_site),
    ]
