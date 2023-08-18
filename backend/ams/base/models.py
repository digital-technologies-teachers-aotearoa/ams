from django.db.models import CharField
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    is_creatable = False
    heading = CharField(blank=True, max_length=255, default="Home")
    subheading = CharField(blank=True, max_length=255, default="")
    body = RichTextField(blank=True, default="Welcome to the homepage")

    content_panels = Page.content_panels + [
        FieldPanel("heading"),
        FieldPanel("subheading"),
        FieldPanel("body"),
    ]


class MembershipPage(Page):
    is_creatable = False
    heading = CharField(blank=True, max_length=255, default="Membership")
    body = RichTextField(
        blank=True, default="<p>You can sign up either individually or for your organisation.  Please select:</p>"
    )

    content_panels = Page.content_panels + [FieldPanel("heading"), FieldPanel("body")]


class EmailConfirmationPage(Page):
    is_creatable = False
    heading = CharField(blank=True, max_length=255, default="Email Confirmation Successful!")
    body = RichTextField(blank=True, default="Congratulations! Your email has been successfully confirmed.")

    content_panels = Page.content_panels + [FieldPanel("heading"), FieldPanel("body")]


class GenericPage(Page):
    is_creatable = True

    heading = CharField(blank=True, max_length=255, default="Heading")
    body = RichTextField(blank=True, default="")

    content_panels = Page.content_panels + [FieldPanel("heading"), FieldPanel("body")]
