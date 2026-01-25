from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.db import models
from django.http import Http404
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.models import Page

from ams.cms.blocks import ContentPageBlocks
from ams.cms.blocks import ContentStreamBlocks
from ams.cms.blocks import HomePageBlocks
from ams.utils.permissions import user_has_active_membership
from ams.utils.reserved_paths import get_reserved_paths_set


class HomePage(Page):
    body = StreamField(
        HomePageBlocks(),
        blank=True,
        use_json_field=True,
        help_text="Content for the home page.",
    )

    # Metadata
    content_panels = [*Page.content_panels, "body"]
    template = "cms/pages/home.html"


class ContentPage(Page):
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_MEMBERS = "members"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_MEMBERS, "Members only"),
    ]

    body = StreamField(
        ContentPageBlocks(),
        blank=True,
        use_json_field=True,
        help_text="Content for this page.",
    )

    visibility = models.CharField(
        max_length=16,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        help_text=(
            "Who can view this page: everyone or only members with active membership.",
        ),
    )

    is_structure_only = models.BooleanField(
        default=False,
        help_text=_(
            "If checked, this page cannot be viewed directly and will redirect to its "
            "first child page.",
        ),
    )

    # Metadata
    content_panels = [
        *Page.content_panels,
        FieldPanel("visibility"),
        FieldPanel("is_structure_only"),
        FieldPanel("body"),
    ]
    template = "cms/pages/content.html"
    parent_page_types = ["cms.HomePage", "cms.ContentPage"]
    subpage_types = ["cms.ContentPage"]
    show_in_menus = True

    def serve(self, request, *args, **kwargs):
        """Override serve to enforce visibility restrictions and handle structure-only
        pages."""
        # Check visibility first
        if self.visibility == self.VISIBILITY_MEMBERS:
            if not user_has_active_membership(request.user):
                return HttpResponseForbidden(
                    "This page is only available to members with an active membership.",
                )

        # Then check if structure-only
        if self.is_structure_only:
            # Find first live descendant (supports multi-level structure pages)
            first_descendant = self.get_descendants().live().first()
            if first_descendant:
                return redirect(first_descendant.url)
            # If no descendants, return 404
            raise Http404(_("This page has no published content."))

        return super().serve(request, *args, **kwargs)

    def clean(self):
        """Validate that the page slug doesn't conflict with reserved URLs."""
        super().clean()

        reserved_paths = get_reserved_paths_set()
        # Only check direct children of HomePage for reserved slug conflicts
        if (
            self.get_parent()
            and self.get_parent().specific.__class__.__name__ == "HomePage"
            and self.slug in reserved_paths
        ):
            raise ValidationError(
                {
                    "slug": f'The slug "{self.slug}" is reserved for application URLs. '
                    f"Please choose a different slug. Reserved slugs are: "
                    f"{', '.join(sorted(reserved_paths))}",
                },
            )


class ArticlesIndexPage(Page):
    """Container page that holds and lists all articles."""

    intro = RichTextField(blank=True)

    subpage_types = ["cms.ArticlePage"]
    parent_page_types = ["cms.HomePage"]
    template = "cms/pages/articles_index_page.html"

    content_panels = [*Page.content_panels, FieldPanel("intro")]

    def get_context(self, request):
        """Add paginated articles to context."""
        context = super().get_context(request)

        # Get all live articles ordered by publication date
        # Only show articles where publication_date <= now()
        articles = (
            ArticlePage.objects.child_of(self)
            .live()
            .select_related("cover_image")
            .filter(publication_date__lte=timezone.now())
            .order_by("-publication_date")
        )

        # Paginate articles (12 per page)
        page = request.GET.get("page", 1)
        paginator = Paginator(articles, 12)

        try:
            articles_page = paginator.page(page)
        except PageNotAnInteger:
            articles_page = paginator.page(1)
        except EmptyPage:
            articles_page = paginator.page(paginator.num_pages)

        context["articles"] = articles_page
        return context


class ArticlePage(Page):
    """Individual article page."""

    publication_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date and time when this article should be published",
    )
    summary = models.CharField(
        max_length=300,
        help_text="Shown on cards that link to the full article",
    )
    author = models.CharField(max_length=255, blank=True)
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Shown on cards that link to the full article",
    )

    body = StreamField(
        ContentStreamBlocks(),
        use_json_field=True,
    )

    parent_page_types = ["cms.ArticlesIndexPage"]
    subpage_types = []
    template = "cms/pages/article_page.html"

    content_panels = [
        *Page.content_panels,
        FieldPanel("publication_date"),
        FieldPanel("cover_image"),
        FieldPanel("author"),
        FieldPanel("summary"),
        FieldPanel("body"),
    ]

    class Meta:
        ordering = ["-publication_date"]
