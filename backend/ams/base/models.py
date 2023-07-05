from django.db.models import CharField
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    heading = CharField(blank=True, max_length=255, default="Home")
    body = RichTextField(blank=True, default="Welcome to the homepage")

    content_panels = Page.content_panels + [
        FieldPanel("heading"),
        FieldPanel("body"),
    ]


class MembershipPage(Page):
    heading = CharField(blank=True, max_length=255, default="Membership")
    body = RichTextField(blank=True, default="Welcome to the membership page")

    content_panels = Page.content_panels + [FieldPanel("heading"), FieldPanel("body")]
