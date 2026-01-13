from django.conf import settings
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.models import register_setting
from wagtail.fields import RichTextField


@register_setting
class SiteSettings(BaseSiteSetting):
    language = models.CharField(
        max_length=10,
        verbose_name="Language",
        blank=True,
        choices=settings.LANGUAGES,
    )

    panels = [
        FieldPanel("language"),
    ]


@register_setting
class AssociationSettings(BaseSiteSetting):
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
    footer_text = RichTextField(
        blank=True,
        features=[
            "bold",
            "italic",
            "link",
            "align-left",
            "align-center",
            "align-right",
            "align-justify",
        ],
        help_text="Optional footer text (e.g., copyright info, disclaimers).",
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
        MultiFieldPanel(
            [
                FieldPanel("footer_text"),
            ],
            "Footer",
        ),
    ]
