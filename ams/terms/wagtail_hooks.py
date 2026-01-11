"""Wagtail hooks for terms app."""

from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from ams.terms.models import Term
from ams.terms.models import TermVersion


class TermViewSet(SnippetViewSet):
    """Custom viewset for Term snippets."""

    model = Term
    list_display = ["name", "key", "created_at"]
    search_fields = ["name", "key", "description"]


class TermVersionViewSet(SnippetViewSet):
    """Custom viewset for TermVersion snippets."""

    model = TermVersion
    list_display = ["term", "version", "is_active", "date_active"]
    list_filter = ["term", "is_active", "date_active"]
    search_fields = ["version", "content"]


# Register the custom viewsets
register_snippet(TermViewSet)
register_snippet(TermVersionViewSet)
