from typing import Any, Dict

from django import template
from django.conf import settings
from django.template.context import RequestContext
from django.utils.translation import get_language

from ..models import Footer

register = template.Library()


@register.inclusion_tag("footer.html", takes_context=True)
def footer(context: RequestContext) -> Dict[str, Any]:
    current_language = get_language()

    footer = Footer.objects.filter(locale__language_code=current_language).order_by("id").first()

    if not footer and current_language != settings.LANGUAGE_CODE:
        # Try to get footer for default language instead
        footer = Footer.objects.filter(locale__language_code=settings.LANGUAGE_CODE).order_by("id").first()

    return {
        "footer": footer,
        "request": context["request"],
    }
