from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import StructBlock
from wagtail.models import Locale

if TYPE_CHECKING:
    from ams.cms.models import ArticlePage


class RecentArticlesBlock(StructBlock):
    """Display most recent published articles in a card grid."""

    article_count = ChoiceBlock(
        choices=[
            ("3", "3 articles"),
            ("6", "6 articles"),
        ],
        default="3",
        help_text="Number of recent articles to display",
    )

    def get_context(self, value, parent_context=None):
        """Add recent articles to context."""
        # Imported here to avoid circular dependencies
        from ams.cms.models import ArticlePage  # noqa: PLC0415

        context = super().get_context(value, parent_context=parent_context)

        count = int(value.get("article_count", 3))

        page = parent_context.get("page") if parent_context else None
        locale = page.locale if page else Locale.get_active()

        articles: list[ArticlePage] = list(
            ArticlePage.objects.live()
            .public()
            .filter(locale=locale)
            .select_related("cover_image")
            .filter(publication_date__lte=timezone.now())
            .order_by("-publication_date")[:count],
        )

        context["articles"] = articles
        return context

    class Meta:
        icon = "doc-full"
        label = "Recent Articles"
        template = "cms/blocks/recent_articles_block.html"
