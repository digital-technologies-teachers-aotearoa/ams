from wagtail.blocks import CharBlock
from wagtail.blocks import StructBlock

from ams.cms.forms import ContactForm


class ContactFormBlock(StructBlock):
    recipient_email = CharBlock(
        help_text="Email address where form submissions will be sent",
    )
    subject = CharBlock(
        required=False,
        help_text="Email subject line (defaults to 'Contact Form Submission')",
    )
    intro_text = CharBlock(
        required=False,
        help_text="Optional introductory text displayed above the form",
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        form_from_context = (
            parent_context.get("contact_form") if parent_context else None
        )
        context["contact_form"] = form_from_context or ContactForm()
        return context

    class Meta:
        icon = "mail"
        label = "Contact Form"
        template = "cms/blocks/contact_form_block.html"
