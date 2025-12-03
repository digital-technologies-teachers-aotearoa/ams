from django.conf.locale import LANG_INFO
from django.http import Http404
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.response import TemplateResponse
from wagtail.models import Site


def bad_request(request, exception=None, template_name="400.html"):
    """Custom 400 error view that provides request context."""
    return HttpResponseBadRequest(render(request, template_name).content)


def permission_denied(request, exception=None, template_name="403.html"):
    """Custom 403 error view that provides request context."""
    return HttpResponseForbidden(render(request, template_name).content)


def server_error(request, template_name="500.html"):
    """Custom 500 error view that provides request context."""
    return HttpResponseServerError(render(request, template_name).content)


def _normalize_path(path, language_code):
    """Strip language prefix from path."""
    if not language_code:
        return path

    prefix = f"/{language_code}/"
    if path.startswith(prefix):
        return path[len(language_code) + 1 :]
    if path == f"/{language_code}":
        return "/"
    return path


def _find_page_in_site(site, path_without_lang, request):
    """Try to find a page at the given path in this site's tree."""
    path_parts = [p for p in path_without_lang.split("/") if p]
    page, _args, _kwargs = site.root_page.specific.route(request, path_parts)
    return page


def _build_locale_info(page, site_language):
    """Build locale information dict for a page."""
    lang_info = LANG_INFO.get(site_language, {})
    return {
        "language": site_language,
        "language_name": lang_info.get("name_local", site_language.upper()),
        "url": page.url_path,
        "title": page.title,
    }


def page_not_found(request, exception=None, template_name="404.html"):
    """
    Custom 404 error view that provides request context and available locales.

    This function-based view maintains APPEND_SLASH functionality while providing
    custom 404 page logic including locale information for pages that exist in
    other sites.
    """
    language_code = getattr(request, "LANGUAGE_CODE", None)
    path_without_lang = _normalize_path(request.path, language_code)
    current_site = getattr(request, "site", None)

    available_locales = []
    sites = Site.objects.select_related("sitesettings").exclude(
        id=current_site.id if current_site else None,
    )

    for site in sites:
        try:
            page = _find_page_in_site(site, path_without_lang, request)
            site_language = getattr(site.sitesettings, "language", None)

            if page and site_language:
                available_locales.append(
                    _build_locale_info(page, site_language),
                )
        except (AttributeError, TypeError, Http404):
            continue

    context = {
        "available_locales": available_locales,
    }

    return TemplateResponse(request, template_name, context, status=404)
