from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.forms import EmailField
from django.forms import Form
from django.forms import ModelForm
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember
from ams.utils.crispy_forms import Cancel


class OrganisationForm(ModelForm):
    """
    Form for creating and editing organisations.
    Validates email format and ensures required fields are filled.
    """

    email = EmailField(
        label=_("Email"),
        required=True,
        validators=[EmailValidator()],
        help_text=_("Organisation contact email address."),
    )

    class Meta:
        model = Organisation
        fields = [
            "name",
            "telephone",
            "email",
            "contact_name",
            "postal_address",
            "postal_suburb",
            "postal_city",
            "postal_code",
            "street_address",
            "suburb",
            "city",
        ]

    def __init__(self, cancel_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        # Determine if we're creating or updating based on instance
        if self.instance and self.instance.pk:
            submit_text = _("Update Organisation")
        else:
            submit_text = _("Create Organisation")
        self.helper.add_layout(
            Layout(
                "name",
                Fieldset(
                    _("Contact"),
                    "contact_name",
                    "email",
                    "telephone",
                ),
                Fieldset(
                    _("Physical address"),
                    "street_address",
                    "suburb",
                    "city",
                ),
                Fieldset(
                    _("Postal address"),
                    "postal_address",
                    "postal_suburb",
                    "postal_city",
                    "postal_code",
                ),
                FormActions(
                    Submit("submit", submit_text, css_class="btn btn-primary"),
                    Cancel(cancel_url),
                ),
            ),
        )

    def clean_email(self):
        """Validate that email is in correct format."""
        email = self.cleaned_data.get("email")
        if email:
            # EmailValidator already validates, convert to lowercase
            return email.lower()
        return email


class InviteOrganisationMemberForm(Form):
    """
    Form for inviting members to an organisation.
    Validates that the email doesn't already belong to an active or invited member.
    """

    email = EmailField(
        label=_("Email"),
        required=True,
        validators=[EmailValidator()],
        help_text=_("Enter the email address of the person you'd like to invite."),
        widget=TextInput(
            attrs={
                "placeholder": _("member@example.com"),
                "autocomplete": "email",
            },
        ),
    )

    def __init__(self, organisation, cancel_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Validate organisation parameter
        if organisation is None:
            message = "organisation is required and cannot be None"
            raise ValueError(message)

        if not isinstance(organisation, Organisation):
            message = (
                f"organisation must be an instance of Organisation, "
                f"got {type(organisation).__name__}"
            )
            raise TypeError(message)

        self.organisation = organisation
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_layout(
            Layout(
                "email",
                FormActions(
                    Submit("submit", _("Send Invite"), css_class="btn btn-primary"),
                    Cancel(cancel_url),
                ),
            ),
        )

    def clean_email(self):
        """Validate that the email is not already a member of the organisation."""
        email = self.cleaned_data.get("email")
        if not email:
            return email

        # Normalize email to lowercase
        email = email.lower()

        if not self.organisation:
            return email

        # Check if user or invite_email already exists for this organisation.
        # Exclude declined and revoked invites - they are deleted immediately
        # when declined/revoked, so this check only finds active/pending invites.
        existing_member = OrganisationMember.objects.filter(
            organisation=self.organisation,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        ).filter(
            user__email=email,
        ) | OrganisationMember.objects.filter(
            organisation=self.organisation,
            invite_email=email,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        )

        if existing_member.exists():
            raise ValidationError(
                _(
                    "This email address is already associated with a member "
                    "of this organisation.",
                ),
                code="duplicate_member",
            )

        return email
