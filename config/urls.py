from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include
from django.urls import path
from django.utils.translation import get_language
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from ams.utils.views import bad_request
from ams.utils.views import page_not_found
from ams.utils.views import permission_denied
from ams.utils.views import server_error


def redirect_to_user_language(request):
    """Redirect to the user's preferred language, falling back to 'en'."""
    language = get_language() or "en"
    return HttpResponseRedirect(f"/{language}/")


urlpatterns = [
    # Redirect root to user's preferred language
    path("", redirect_to_user_language, name="root_redirect"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Billing webhooks (Xero, etc)
    path("billing/", include("ams.billing.urls", namespace="billing")),
    # CMS
    path("cms/", include(wagtailadmin_urls)),
    path("cms-documents/", include(wagtaildocs_urls)),
    # Forum
    path("forum/", include("ams.forum.urls", namespace="forum")),
]

urlpatterns += i18n_patterns(
    # User management
    path(
        "users/memberships/",
        include("ams.memberships.urls", namespace="memberships"),
    ),
    path("accounts/", include("allauth.urls")),
    path("users/", include("ams.users.urls", namespace="users")),
    path(
        "organisations/",
        include("ams.organisations.urls", namespace="organisations"),
    ),
    # Terms and conditions
    path("terms/", include("ams.terms.urls", namespace="terms")),
    # CMS pages are handled by Wagtail
    path("", include(wagtail_urls)),
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path("400/", bad_request),
        path("403/", permission_denied),
        path("404/", page_not_found),
        path("500/", server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]


# Set custom error handlers
# Use string paths for error handlers to maintain APPEND_SLASH functionality
handler400 = "ams.utils.views.bad_request"
handler403 = "ams.utils.views.permission_denied"
handler404 = "ams.utils.views.page_not_found"
handler500 = "ams.utils.views.server_error"
