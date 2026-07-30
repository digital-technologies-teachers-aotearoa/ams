"""Module for the custom Django prune_resource_views command."""

from datetime import timedelta

from django.conf import settings
from django.core import management
from django.utils import timezone

from ams.resources.models import ResourceComponentView
from ams.resources.models import ResourceView
from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django prune_resource_views command."""

    help = (
        "Delete ResourceView and ResourceComponentView rows older than the "
        f"retention window (default {settings.RESOURCE_VIEW_RETENTION_DAYS} "
        "days, override with RESOURCE_VIEW_RETENTION_DAYS). Denormalised "
        "view_count totals are unaffected."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=settings.RESOURCE_VIEW_RETENTION_DAYS,
            help="Delete view rows older than this many days.",
        )

    def handle(self, *args, **options):
        """Automatically called when the prune_resource_views command is given."""
        self.stdout.write(LOG_HEADER.format("🧹 Prune resource views"))
        cutoff = timezone.now() - timedelta(days=options["days"])

        resource_views, _ = ResourceView.objects.filter(
            datetime_viewed__lt=cutoff,
        ).delete()
        component_views, _ = ResourceComponentView.objects.filter(
            datetime_viewed__lt=cutoff,
        ).delete()

        self.stdout.write(
            f"✅ Deleted {resource_views} resource view rows and "
            f"{component_views} component view rows older than "
            f"{options['days']} days.",
        )
