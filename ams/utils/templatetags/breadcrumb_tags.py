"""Template tags for rendering breadcrumbs."""

from django import template
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from ams.cms.models import HomePage
from ams.utils.breadcrumbs import get_breadcrumbs_for_django_page
from ams.utils.breadcrumbs import get_current_view_name
from ams.utils.breadcrumbs import is_homepage

register = template.Library()

WAGTAIL_MINIMUM_DEPTH = 2


@register.inclusion_tag("includes/breadcrumbs.html", takes_context=True)
def breadcrumbs(context):
    """
    Renders breadcrumbs for current page (Django or Wagtail).
    Returns empty if homepage.
    """
    request = context["request"]

    # Check if homepage - no breadcrumbs
    if is_homepage(request):
        return {"breadcrumbs": []}

    breadcrumb_list = []

    # Check if Wagtail page
    if "page" in context:
        page = context["page"]

        # Skip if homepage
        if isinstance(page, HomePage):
            return {"breadcrumbs": []}

        # Build breadcrumbs from Wagtail hierarchy
        ancestors = page.get_ancestors().live()

        # Add home
        breadcrumb_list.append(
            {
                "url": "/",
                "title": _("Home"),
                "is_active": False,
            },
        )

        # Add ancestors (skip root/HomePage)
        # In Wagtail: depth=1 is root, depth=2 is HomePage, depth=3+ are content pages
        for ancestor in ancestors:
            if ancestor.depth > WAGTAIL_MINIMUM_DEPTH:
                # Check if structure-only
                is_structure_only = getattr(
                    ancestor.specific,
                    "is_structure_only",
                    False,
                )
                breadcrumb_list.append(
                    {
                        "url": None if is_structure_only else ancestor.url,
                        "title": ancestor.title,
                        "is_active": False,
                    },
                )

        # Add current page
        breadcrumb_list.append(
            {
                "url": None,
                "title": page.title,
                "is_active": True,
            },
        )

    # Otherwise, Django view
    else:
        view_name = get_current_view_name(request)
        if view_name:
            resolved = resolve(request.path_info)
            breadcrumb_list = get_breadcrumbs_for_django_page(
                request,
                view_name,
                **resolved.kwargs,
            )

    return {"breadcrumbs": breadcrumb_list}
