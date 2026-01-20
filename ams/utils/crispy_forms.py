from crispy_forms.layout import Field
from crispy_forms.layout import LayoutObject
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class Cancel(LayoutObject):
    """Layout object that displays a cancel button.

    Uses an <a> tag for correct HTML syntax.

    url (str): A URL for the Cancel button link to target.
    """

    TEMPLATE = "utils/crispy_forms/cancel.html"

    def __init__(self, url=None, **kwargs):
        if url:
            self.url = url
        else:
            self.url = reverse("root_redirect")

    def render(self, form, context, **kwargs):
        return render_to_string(
            self.TEMPLATE,
            {
                "url": self.url,
            },
        )


class PricingCardsRadio(LayoutObject):
    """Renders ModelChoiceField as Bootstrap pricing cards with radio buttons.

    Designed for MembershipOption selection with full model data display.

    Args:
        field_name (str): Name of the field to render
        show_org_fields (bool): Show organisation-specific fields
    """

    TEMPLATE = "utils/crispy_forms/card_radio.html"

    def __init__(self, field_name, show_org_fields=False, **kwargs):  # noqa: FBT002
        self.field_name = field_name
        self.show_org_fields = show_org_fields

    def render(self, form, context, **kwargs):
        field = form[self.field_name]
        return render_to_string(
            self.TEMPLATE,
            {
                "field": field,
                "show_org_fields": self.show_org_fields,
            },
        )


class ProfileFieldWithBadges(LayoutObject):
    """Renders a form field with badge indicators for profile field metadata.

    Modifies the field label to include badges, then delegates rendering
    to crispy forms' standard Field object.

    Displays badges to indicate:
    - Recommended (counts toward profile completion) - Blue badge
    - Required for membership (needed before membership purchase) - Yellow badge

    Args:
        field_name: Name of the field to render
        profile_field: The ProfileField model instance with metadata
    """

    def __init__(self, field_name, profile_field=None, **kwargs):
        self.field_name = field_name
        self.profile_field = profile_field

    def render(self, form, context, **kwargs):
        """Render field with badges in label, delegating to standard Field renderer."""
        bound_field = form[self.field_name]

        # Build badge HTML
        badges = []

        if (
            self.profile_field
            and self.profile_field.counts_toward_completion
            and not bound_field.field.required
        ):
            badges.append(
                '<span class="badge bg-primary">{}</span>'.format(_("Recommended")),
            )

        if self.profile_field and self.profile_field.is_required_for_membership:
            badges.append(
                '<span class="badge bg-warning text-dark">{}</span>'.format(
                    _("Required for membership"),
                ),
            )

        # Modify the field label to include badges
        original_label = bound_field.label
        if badges:
            badge_html = " ".join(badges)
            bound_field.label = mark_safe(f"{original_label} {badge_html}")  # noqa: S308

        # Delegate to standard Field renderer
        field_obj = Field(self.field_name)
        return field_obj.render(form, context, **kwargs)
