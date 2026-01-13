from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.rich_text.converters.html_to_contentstate import BlockElementHandler
from wagtail.admin.rich_text.editors.draftail.features import BlockFeature
from wagtail.admin.ui.components import Component
from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.pages import PageListingViewSet

from ams.cms.models.pages import ArticlePage
from ams.utils.permissions import user_has_active_membership


@hooks.register("register_icons")
def register_icons(icons):
    return [
        *icons,
        "cms/wagtail-icons/align-left.svg",
        "cms/wagtail-icons/align-center.svg",
        "cms/wagtail-icons/align-right.svg",
        "cms/wagtail-icons/align-justify.svg",
    ]


class ArticlePageListingViewSet(PageListingViewSet):
    icon = "calendar-alt"
    menu_label = "Articles"
    add_to_admin_menu = True
    model = ArticlePage
    columns = [
        *PageListingViewSet.columns,
        Column(
            "publication_date",
            label="Publication Date",
            sort_key="publication_date",
        ),
        Column(
            "author",
            label="Author",
            sort_key="author",
        ),
    ]


article_page_listing_viewset = ArticlePageListingViewSet("article_pages")


@hooks.register("register_admin_viewset")
def register_article_page_listing_viewset():
    return article_page_listing_viewset


@hooks.register("construct_help_menu")
def add_ams_help_menu_item(request, menu_items):
    """Add AMS help link to the Wagtail admin help menu."""
    menu_items.append(
        MenuItem(
            _("AMS help"),
            f"{settings.DOCUMENTATION_URL}/admin/cms/",
            name="ams_help",
            icon_name="help",
            attrs={"target": "_blank", "rel": "noopener noreferrer"},
        ),
    )


@hooks.register("before_serve_document")
def check_document_permissions(document, request):
    """Check permissions before serving a document."""
    if request.user.is_superuser or user_has_active_membership(request.user):
        return None
    # Else show error and redirect to login
    messages.error(
        request,
        "You must have an active membership to view this file",
    )
    return redirect("account_login")


if settings.WAGTAIL_AMS_ADMIN_HELPERS:

    class WelcomePanel(Component):
        order = 10

        def render_html(self, parent_context):
            return render_to_string(
                "wagtail/homepage-welcome.html",
                {"DOCUMENTATION_URL": settings.DOCUMENTATION_URL},
            )

    @hooks.register("construct_homepage_panels")
    def add_another_welcome_panel(request, panels):
        panels.append(WelcomePanel())

    @hooks.register("insert_global_admin_css")
    def global_admin_css():
        return format_html(
            """
            <link rel="stylesheet" href="{}">
            <link rel="stylesheet" href="{}">
            """,
            static("css/wagtail-admin.css"),
            static("css/wagtail-admin-helpers.min.css"),
        )

    @hooks.register("insert_global_admin_js")
    def global_admin_js():
        return format_html(
            '<script src="{}"></script>',
            static("js/wagtail-admin-helpers.min.js"),
        )


ALIGNMENTS = {
    "align-left": {
        "icon": "align-left",
        "description": "Align left",
    },
    "align-center": {
        "icon": "align-center",
        "description": "Align center",
    },
    "align-right": {
        "icon": "align-right",
        "description": "Align right",
    },
    "align-justify": {
        "icon": "align-justify",
        "description": "Justify",
    },
}


@hooks.register("register_rich_text_features")
def register_alignment_features(features):
    for classname, control in ALIGNMENTS.items():
        feature_name = classname
        block_type = classname.upper().replace("-", "_")

        features.register_editor_plugin(
            "draftail",
            feature_name,
            BlockFeature(
                {
                    "type": block_type,
                    "icon": control["icon"],
                    "description": control["description"],
                },
            ),
        )

        features.register_converter_rule(
            "contentstate",
            feature_name,
            {
                "from_database_format": {
                    f'p[class="{classname}"]': BlockElementHandler(block_type),
                },
                "to_database_format": {
                    "block_map": {
                        block_type: {
                            "element": "p",
                            "props": {"class": classname},
                        },
                    },
                },
            },
        )

        features.default_features.append(feature_name)
