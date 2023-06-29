from django.db.models import CharField
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    heading = CharField(blank=True, max_length=255)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("heading"), FieldPanel("body")]
