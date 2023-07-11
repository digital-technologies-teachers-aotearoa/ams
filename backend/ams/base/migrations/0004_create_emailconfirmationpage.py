# -*- coding: utf-8 -*-
from typing import Any

from django.db import migrations
from wagtail.models import Page


def create_email_confirmation_page(apps: Any, schema_editor: Any) -> None:
    EmailConfirmationPage = apps.get_model("base.EmailConfirmationPage")
    ContentType = apps.get_model("contenttypes.ContentType")
    Locale = apps.get_model("wagtailcore.Locale")

    default_locale = Locale.objects.get(pk=1)
    content_type, __ = ContentType.objects.get_or_create(model="emailconfirmationpage", app_label="base")

    email_confirmation_page = EmailConfirmationPage(
        locale_id=default_locale.id, title="Email Confirmed", slug="email-confirmed", content_type=content_type
    )
    home_page = Page.objects.get(slug="home")
    home_page.add_child(instance=email_confirmation_page)


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0003_create_membershippage"),
    ]

    operations = [
        migrations.RunPython(create_email_confirmation_page),
    ]
