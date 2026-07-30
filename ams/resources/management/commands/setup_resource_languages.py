"""Management command to seed the "Language" resource category and its tags."""

from django.conf import settings
from django.core.management.base import BaseCommand

from ams.resources.models import ResourceCategory
from ams.resources.models import ResourceTag
from ams.utils.management.commands._constants import LOG_HEADER

LANGUAGE_CATEGORY_SLUG = "language"

# Each tuple is (name, abbreviation, order).
LANGUAGE_TAGS: list[tuple[str, str, int]] = [
    ("English", "EN", 1),
    ("Te Reo Māori", "MI", 2),
]


class Command(BaseCommand):
    help = "Idempotently create the Language resource category and its seed tags."

    def handle(self, *args, **options):
        self.stdout.write(LOG_HEADER.format("🌐 Set up resource languages"))

        if not settings.RESOURCES_ENABLED:
            self.stdout.write("Resources module disabled, skipping.")
            return

        category, created = ResourceCategory.objects.get_or_create(
            slug=LANGUAGE_CATEGORY_SLUG,
            defaults={
                "name": "Language",
                "name_en": "Language",
                "name_mi": "Reo",
                "order": 0,
            },
        )
        if not created:
            self.stdout.write("Language category already exists, skipping.")
            return

        for name, abbreviation, order in LANGUAGE_TAGS:
            ResourceTag.objects.create(
                category=category,
                name=name,
                name_en=name,
                name_mi=name,
                abbreviation=abbreviation,
                abbreviation_en=abbreviation,
                abbreviation_mi=abbreviation,
                order=order,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Created Language category with {len(LANGUAGE_TAGS)} tags.",
            ),
        )
