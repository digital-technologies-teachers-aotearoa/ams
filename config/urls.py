from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/memberships/",
        include("ams.memberships.urls", namespace="memberships"),
    ),
    path("users/", include("ams.users.urls", namespace="users")),
    path("billing/", include("ams.billing.urls", namespace="billing")),
    path("accounts/", include("allauth.urls")),
    # CMS
    path("cms/", include(wagtailadmin_urls)),
    path("cms-documents/", include(wagtaildocs_urls)),
    # Forum
    path("forum/", include("ams.forum.urls", namespace="forum")),
    # All other pages are handled by Wagtail
    path("", include(wagtail_urls)),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
