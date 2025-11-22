from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting
from wagtail.contrib.settings.models import register_setting
from wagtail.documents.models import AbstractDocument
from wagtail.documents.models import Document
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.models import Page

from ams.cms.blocks import ContentAndLayoutStreamBlocks
from ams.utils.permissions import user_has_active_membership

# Reserved URL patterns that cannot be used as page slugs
RESERVED_URL_SLUGS = {
    "billing",
    "users",
    "forum",
    "cms",
    "cms-documents",
    "accounts",
}


class HomePage(Page):
    lead_paragraph = RichTextField(blank=True)

    # Metadata
    max_count = 1
    content_panels = [*Page.content_panels, "lead_paragraph"]
    template = "cms/pages/home.html"


class ContentPage(Page):
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_MEMBERS = "members"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_MEMBERS, "Members only"),
    ]

    body = StreamField(
        ContentAndLayoutStreamBlocks(),
        blank=True,
        use_json_field=True,
        help_text="Content for the about page.",
    )

    visibility = models.CharField(
        max_length=16,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        help_text=(
            "Who can view this page: everyone or only members with active membership.",
        ),
    )

    # Metadata
    content_panels = [
        *Page.content_panels,
        FieldPanel("visibility"),
        FieldPanel("body"),
    ]
    template = "cms/pages/content.html"
    parent_page_types = ["cms.HomePage", "cms.ContentPage"]
    subpage_types = ["cms.ContentPage"]
    show_in_menus = True

    def serve(self, request, *args, **kwargs):
        """Override serve to enforce visibility restrictions."""
        if self.visibility == self.VISIBILITY_MEMBERS:
            if not user_has_active_membership(request.user):
                return HttpResponseForbidden(
                    "This page is only available to members with an active membership.",
                )
        return super().serve(request, *args, **kwargs)

    def clean(self):
        """Validate that the page slug doesn't conflict with reserved URLs."""
        super().clean()

        # Only check direct children of HomePage for reserved slug conflicts
        if (
            self.get_parent()
            and self.get_parent().specific.__class__.__name__ == "HomePage"
            and self.slug in RESERVED_URL_SLUGS
        ):
            raise ValidationError(
                {
                    "slug": f'The slug "{self.slug}" is reserved for application URLs. '
                    f"Please choose a different slug. Reserved slugs are: "
                    f"{', '.join(sorted(RESERVED_URL_SLUGS))}",
                },
            )


@register_setting
class AssociationSettings(BaseGenericSetting):
    association_short_name = models.CharField(
        max_length=255,
        verbose_name="Association short name",
        blank=True,
    )
    association_long_name = models.CharField(
        max_length=255,
        verbose_name="Association long name",
        blank=True,
    )
    association_logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Association logo",
    )
    association_favicon = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Association favicon",
    )
    use_logo_in_navbar = models.BooleanField(
        default=False,
        verbose_name="Use logo in navbar",
        help_text="If not set, the association short name will be used in the navbar.",
    )
    use_logo_in_footer = models.BooleanField(
        default=False,
        verbose_name="Use logo in footer",
        help_text="If not set, the association short name will be used in the footer.",
    )
    linkedin_url = models.URLField(
        verbose_name="LinkedIn URL",
        blank=True,
        help_text="If set, a link will appear in the footer.",
    )
    facebook_url = models.URLField(
        verbose_name="Facebook URL",
        blank=True,
        help_text="If set, a link will appear in the footer.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("association_short_name"),
                FieldPanel("association_long_name"),
            ],
            "Name",
        ),
        MultiFieldPanel(
            [
                FieldPanel("association_logo"),
                FieldPanel("use_logo_in_navbar"),
                FieldPanel("use_logo_in_footer"),
                FieldPanel("association_favicon"),
            ],
            "Images",
        ),
        MultiFieldPanel(
            [
                FieldPanel("linkedin_url"),
                FieldPanel("facebook_url"),
            ],
            "Social networks",
        ),
    ]


class AMSDocument(AbstractDocument):
    """Custom Document model that stores to private storage."""

    file = models.FileField(
        storage=storages["private"],
        upload_to="documents",
        verbose_name=_("file"),
    )

    admin_form_fields = Document.admin_form_fields
