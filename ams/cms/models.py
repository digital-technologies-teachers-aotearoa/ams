from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting
from wagtail.contrib.settings.models import register_setting
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.models import Page

from ams.cms.blocks import BaseStreamBlock


class HomePage(Page):
    lead_paragraph = RichTextField(blank=True)

    # Metadata
    max_count = 1
    content_panels = [*Page.content_panels, "lead_paragraph"]
    template = "cms/pages/home.html"


class ContentPage(Page):
    body = StreamField(
        BaseStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text="Content for the about page.",
    )

    # Metadata
    content_panels = [*Page.content_panels, FieldPanel("body")]
    template = "cms/pages/content.html"
    parent_page_types = ["cms.HomePage", "cms.ContentPage"]
    subpage_types = ["cms.ContentPage"]
    show_in_menus = True


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
