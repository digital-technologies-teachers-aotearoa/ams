import logging
from typing import Any

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.forms import BooleanField
from django.forms import CharField
from django.forms import ChoiceField
from django.forms import DateField
from django.forms import DateInput
from django.forms import DecimalField
from django.forms import IntegerField
from django.forms import ModelChoiceField
from django.forms import ModelForm
from django.forms import MultiValueField
from django.forms import MultiWidget
from django.forms import Select
from django.forms import TextInput
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ams.billing.models import Account
from ams.billing.services.membership import MembershipBillingService
from ams.memberships.duration import compose_membership_duration
from ams.memberships.duration import decompose_membership_duration
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.memberships.models import OrganisationMembership
from ams.organisations.models import Organisation
from ams.utils.crispy_forms import Cancel


class MembershipDurationWidget(MultiWidget):
    def __init__(
        self,
        choices: list[tuple[str, str]],
        attrs: dict[str, Any] | None = None,
    ) -> None:
        widgets = (
            TextInput(attrs=attrs),
            Select(attrs=attrs, choices=choices),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value: relativedelta | None) -> list[Any]:
        if value:
            unit, count = decompose_membership_duration(value)
            return [unit, count]
        return [None, None]


class MembershipDurationField(MultiValueField):
    choices = [
        ("days", _("Days")),
        ("weeks", _("Weeks")),
        ("months", _("Months")),
        ("years", _("Years")),
    ]

    def __init__(self, *args: Any, **kwargs: Any):
        fields = (
            IntegerField(min_value=1),
            ChoiceField(choices=self.choices),
        )
        super().__init__(fields, *args, **kwargs)
        self.widget = MembershipDurationWidget(
            choices=self.choices,
            attrs={"class": "membership-duration"},
        )

    def compress(self, data_list: list[Any]) -> relativedelta | None:
        if data_list:
            num, unit = data_list
            if num is not None and unit:
                num = int(num)
                return compose_membership_duration(num, unit)
        return None


class MembershipOptionForm(ModelForm):
    name = CharField(label=_("Name"), max_length=255)
    type = ChoiceField(
        label=_("Type"),
        choices=MembershipOptionType.choices,
    )
    duration = MembershipDurationField(label=_("Duration"))
    cost = DecimalField(label=_("Cost"))
    invoice_reference = CharField(
        label=_("Invoice Reference"),
        max_length=25,
        required=False,
        help_text=_(
            "What displays as the reference for any generated invoices. "
            "For example 'DTTA Membership'.",
        ),
    )
    max_seats = DecimalField(
        max_digits=10,
        decimal_places=0,
        required=False,
        help_text=_(
            "Maximum number of seats for organisation memberships (optional limit)",
        ),
    )
    archived = BooleanField(
        required=False,
        help_text=_("Mark as archived to prevent new signups"),
    )

    class Meta:
        model = MembershipOption
        fields = [
            "name",
            "type",
            "duration",
            "cost",
            "invoice_reference",
            "max_seats",
            "archived",
        ]


class CreateIndividualMembershipForm(ModelForm):
    """Form a user uses to create an individual membership.

    Only exposes the membership option. The user is implicitly the
    authenticated user submitting the form. We restrict options to
    INDIVIDUAL type membership options.
    """

    membership_option = ModelChoiceField(
        label=_("Membership option"),
        queryset=MembershipOption.objects.filter(
            type=MembershipOptionType.INDIVIDUAL,
            archived=False,
        ).order_by("cost"),
        empty_label=None,
    )
    start_date = DateField(
        label=_("Start date"),
        widget=DateInput(attrs={"type": "date"}),
        initial=timezone.localdate,
        required=True,
    )

    class Meta:
        model = IndividualMembership
        fields = ["membership_option", "start_date"]

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "membership_option",
            "start_date",
            HTML("""
                {% load i18n %}
                <div class="mb-3">
                    <p>
                        <strong>{% translate "End date" %}:</strong>
                        <span id="membership-end-date">—</span>
                    </p>
                </div>
            """),
            Submit("submit", "Register membership", css_class="btn btn-primary"),
        )

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if self.user and start_date:
            overlapping = IndividualMembership.objects.filter(
                user=self.user,
                cancelled_datetime__isnull=True,
                start_date__lte=start_date,
                expiry_date__gt=start_date,
            )
            # Exclude self if updating
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise ValidationError(
                    _(
                        "You already have a non-cancelled membership active"
                        " on this start date.",
                    ),
                )
        return start_date

    def save(self, user=None):
        """Create an IndividualMembership bound to provided user.

        Args:
            commit: whether to write to DB.
            user: The authenticated user applying. Required.
        Raises:
            ValidationError: If billing account or invoice creation fails.
        """
        logger = logging.getLogger(__name__)

        if user is None:
            msg = "user must be provided when saving the form"
            raise ValueError(msg)
        instance: IndividualMembership = super().save(commit=False)
        instance.user = user
        instance.expiry_date = instance.calculate_expiry_date()
        instance.created_datetime = timezone.now()

        membership_option = instance.membership_option
        if membership_option.cost and membership_option.cost > 0:
            try:
                account, _created = Account.objects.get_or_create(user=user)
            except Exception as e:
                logger.exception(
                    "Failed to get or create billing account for user %s",
                    user.username,
                )
                raise ValidationError(
                    _("Could not create billing account. Please contact us."),
                ) from e

            # Create invoice using billing service
            billing_service = MembershipBillingService()
            try:
                invoice = billing_service.create_membership_invoice(
                    account,
                    membership_option,
                )
                if invoice:
                    instance.invoice = invoice
            except Exception as e:
                logger.exception("Failed to create invoice for user %s", user.pk)
                raise ValidationError(
                    _(
                        "Could not create invoice for your "
                        "membership. Please contact us.",
                    ),
                ) from e
        else:
            # Zero-cost membership: automatically approve
            instance.approved_datetime = timezone.now()
            logger.info(
                "Auto-approving zero-cost membership for user %s with option %s",
                user.pk,
                membership_option.name,
            )

        instance.save()
        return instance


class CreateOrganisationMembershipForm(ModelForm):
    """Form for creating a new membership for an organisation.

    Allows selection of membership option and number of seats, with overlap validation.
    """

    membership_option = ModelChoiceField(
        label=_("Membership option"),
        queryset=MembershipOption.objects.filter(
            type=MembershipOptionType.ORGANISATION,
            archived=False,
        ).order_by("cost"),
        empty_label=None,
        help_text=_("Select the type of membership for this organisation."),
    )
    start_date = DateField(
        label=_("Start date"),
        widget=DateInput(attrs={"type": "date"}),
        required=True,
        help_text=_("The date this membership becomes active."),
    )
    seat_count = IntegerField(
        label=_("Number of seats"),
        min_value=1,
        initial=1,
        help_text=_("How many member seats should be included in this membership?"),
    )

    class Meta:
        model = OrganisationMembership
        fields = ["membership_option", "start_date", "seat_count"]

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

        # Set default start date: today or latest expiry if there's an active membership
        latest_membership = (
            organisation.organisation_memberships.filter(
                cancelled_datetime__isnull=True,
            )
            .order_by("-expiry_date")
            .first()
        )

        if latest_membership:
            # Default to the day after the latest membership expires
            self.fields["start_date"].initial = latest_membership.expiry_date
        else:
            # Default to today
            self.fields["start_date"].initial = timezone.localdate()

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_layout(
            Layout(
                "membership_option",
                "start_date",
                "seat_count",
                HTML("""
                    {% load i18n %}
                    <div class="mb-3">
                        <p>
                            <strong>{% translate "Expiry date" %}:</strong>
                            <span id="membership-expiry-date">—</span>
                        </p>
                        <p>
                            <strong>{% translate "Total cost" %}:</strong>
                            <span id="membership-total-cost">—</span>
                        </p>
                    </div>
                """),
                FormActions(
                    Submit("submit", _("Add Membership"), css_class="btn btn-primary"),
                    Cancel(cancel_url),
                ),
            ),
        )

    def clean_seat_count(self):
        """Validate that seat count doesn't exceed max_seats if defined."""
        seat_count = self.cleaned_data.get("seat_count")
        membership_option = self.cleaned_data.get("membership_option")

        if membership_option and membership_option.max_seats:
            max_seats = int(membership_option.max_seats)
            if seat_count > max_seats:
                raise ValidationError(
                    _(
                        "Seat count (%(count)s) cannot exceed the maximum seats "
                        "(%(max)s) for this membership option.",
                    )
                    % {"count": seat_count, "max": max_seats},
                    code="seat_count_exceeds_max",
                )

        return seat_count

    def clean_start_date(self):
        """Validate that start_date doesn't overlap with active/pending memberships."""
        start_date = self.cleaned_data.get("start_date")

        if self.organisation and start_date:
            # Get all non-cancelled memberships for this organisation
            overlapping = OrganisationMembership.objects.filter(
                organisation=self.organisation,
                cancelled_datetime__isnull=True,
                start_date__lte=start_date,
                expiry_date__gt=start_date,
            )

            # Exclude self if updating (though we're only creating for now)
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise ValidationError(
                    _(
                        "This start date overlaps with an existing non-cancelled "
                        "membership. Please choose a date on or after the current "
                        "membership's expiry date.",
                    ),
                    code="overlapping_membership",
                )

        return start_date

    def save(self, commit=True):  # noqa: FBT002
        """Create an OrganisationMembership with invoice if billing is configured.

        Args:
            commit: whether to write to DB.

        Returns:
            OrganisationMembership: The created membership instance.

        Raises:
            ValidationError: If billing account or invoice creation fails.
        """
        logger = logging.getLogger(__name__)

        instance = super().save(commit=False)
        instance.organisation = self.organisation
        instance.expiry_date = instance.calculate_expiry_date()
        instance.created_datetime = timezone.now()

        # Get seat count from cleaned data
        seat_count = self.cleaned_data.get("seat_count", 1)

        # Set max_seats on the membership instance
        instance.max_seats = seat_count

        membership_option = instance.membership_option

        if membership_option.cost > 0:
            # Get or create billing account for the organisation
            try:
                account, _created = Account.objects.get_or_create(
                    organisation=self.organisation,
                )
            except Exception as e:
                logger.exception(
                    "Failed to get or create billing account for organisation %s",
                    self.organisation.uuid,
                )
                raise ValidationError(
                    _("Could not create billing account. Please contact us."),
                ) from e

            # Create invoice using billing service
            billing_service = MembershipBillingService()
            try:
                invoice = billing_service.create_membership_invoice(
                    account,
                    membership_option,
                    seat_count,
                )
                if invoice:
                    instance.invoice = invoice
                    logger.info(
                        "Created invoice %s for organisation %s",
                        invoice.invoice_number,
                        self.organisation.uuid,
                    )
            except Exception as e:
                logger.exception(
                    "Failed to create invoice for organisation %s",
                    self.organisation.uuid,
                )
                raise ValidationError(
                    _(
                        "Could not create invoice for the membership. "
                        "Please contact us.",
                    ),
                ) from e

        if commit:
            instance.save()

        return instance
