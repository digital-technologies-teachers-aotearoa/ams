# -*- coding: utf-8 -*-
from typing import Any

from django.db import migrations
from wagtail.models import Page


def create_membership_page(apps: Any, schema_editor: Any) -> None:
    MembershipPage = apps.get_model("base.MembershipPage")
    ContentType = apps.get_model("contenttypes.ContentType")
    Locale = apps.get_model("wagtailcore.Locale")

    default_locale = Locale.objects.get(pk=1)
    content_type, __ = ContentType.objects.get_or_create(model="membershippage", app_label="base")

    membership_page = MembershipPage(
        locale_id=default_locale.id, title="Membership", slug="membership", content_type=content_type
    )
    home_page = Page.objects.get(slug="home")
    home_page.add_child(instance=membership_page)


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0002_create_homepage"),
    ]

    operations = [
        migrations.RunPython(create_membership_page),
    ]
