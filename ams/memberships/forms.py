import logging
from decimal import Decimal
from typing import Any

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import BooleanField
from django.forms import CharField
from django.forms import ChoiceField
from django.forms import DateField
from django.forms import DateInput
from django.forms import DecimalField
from django.forms import Form
from django.forms import IntegerField
from django.forms import ModelChoiceField
from django.forms import ModelForm
from django.forms import MultiValueField
from django.forms import MultiWidget
from django.forms import NumberInput
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
from ams.memberships.services import calculate_prorata_seat_cost
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
    invoice_due_days = IntegerField(
        label=_("Invoice Due Days"),
        initial=60,
        min_value=1,
        help_text=_(
            "Number of days from invoice issue date until payment is due. "
            "This setting only affects new invoices created after changes are saved.",
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
            "invoice_due_days",
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
                # Save instance first to get primary key
                instance.save()

                invoice = billing_service.create_membership_invoice(
                    account,
                    membership_option,
                    membership=instance,
                )
                if invoice:
                    logger.info(
                        "Created invoice %s for user %s",
                        invoice.invoice_number,
                        self.user.uuid,
                    )
            except Exception as e:
                logger.exception("Failed to create invoice for user %s", user.pk)
                raise ValidationError(
                    _(
                        "Could not create invoice for your "
                        "membership. Please contact us.",
                    ),
                ) from e
        else:
            # Zero-cost membership
            if settings.REQUIRE_FREE_MEMBERSHIP_APPROVAL:
                logger.info(
                    "Zero-cost membership created pending approval "
                    "for user %s with option %s",
                    user.pk,
                    membership_option.name,
                )
            else:
                # Auto-approve
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

        # Default to the day after the latest membership expires,
        # but only if that expiry is in the future. If the latest
        # expiry is today or in the past, default to today instead.
        today = timezone.localdate()
        if latest_membership:
            expiry = latest_membership.expiry_date
            if expiry and expiry > today:
                self.fields["start_date"].initial = expiry
            else:
                self.fields["start_date"].initial = today
        else:
            self.fields["start_date"].initial = today

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

        # Check that seat count includes all current active organisation members
        if self.organisation and seat_count:
            active_member_count = (
                self.organisation.organisation_members.active().count()
            )
            if seat_count < active_member_count:
                raise ValidationError(
                    _(
                        "Seat count (%(count)s) must be at least %(required)s to "
                        "include all current active organisation members.",
                    )
                    % {"count": seat_count, "required": active_member_count},
                    code="insufficient_seats_for_members",
                )

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

        # Set seats on the membership instance
        instance.seats = seat_count

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
                # Save instance first to get primary key (but not committed yet)
                instance.save()

                invoice = billing_service.create_membership_invoice(
                    account,
                    membership_option,
                    seat_count,
                    membership=instance,
                )
                if invoice:
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
        else:
            # Zero-cost membership
            if settings.REQUIRE_FREE_MEMBERSHIP_APPROVAL:
                logger.info(
                    "Zero-cost membership created pending approval "
                    "for organisation %s with option %s",
                    self.organisation.uuid,
                    membership_option.name,
                )
            else:
                # Auto-approve
                instance.approved_datetime = timezone.now()
                logger.info(
                    "Auto-approving zero-cost organisation membership for "
                    "organisation %s with option %s",
                    self.organisation.uuid,
                    membership_option.name,
                )

            if commit:
                instance.save()

        return instance


class AddOrganisationSeatsForm(Form):
    """
    Form for purchasing additional seats mid-term with pro-rata pricing.
    Calculates pro-rated cost based on remaining membership period.
    """

    seats_to_add = IntegerField(
        label=_("Number of Seats to Add"),
        required=True,
        min_value=1,
        help_text=_("Enter the number of additional seats to purchase."),
        widget=NumberInput(
            attrs={
                "min": "1",
                "class": "form-control",
            },
        ),
    )

    def __init__(
        self,
        organisation,
        active_membership,
        cancel_url=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Validate parameters
        if organisation is None:
            message = "organisation is required and cannot be None"
            raise ValueError(message)

        if not isinstance(organisation, Organisation):
            message = (
                f"organisation must be an instance of Organisation, "
                f"got {type(organisation).__name__}"
            )
            raise TypeError(message)

        if active_membership is None:
            message = "active_membership is required and cannot be None"
            raise ValueError(message)

        self.organisation = organisation
        self.active_membership = active_membership
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_layout(
            Layout(
                "seats_to_add",
                FormActions(
                    Submit("submit", _("Purchase Seats"), css_class="btn btn-success"),
                    Cancel(cancel_url),
                ),
            ),
        )

    def clean_seats_to_add(self):
        """Validate seats_to_add is positive and membership has sufficient time
        remaining."""
        seats_to_add = self.cleaned_data.get("seats_to_add")

        if seats_to_add is None:
            return seats_to_add

        if seats_to_add <= 0:
            raise ValidationError(
                _("Number of seats must be greater than zero."),
                code="invalid_seat_count",
            )

        # Check if membership has at least 1 day remaining
        today = timezone.localdate()
        days_remaining = (self.active_membership.expiry_date - today).days

        if days_remaining < 1:
            raise ValidationError(
                _(
                    "Cannot add seats - membership expires too soon. "
                    "Please renew your membership first.",
                ),
                code="membership_expiring",
            )

        # Check if adding seats would exceed the membership option's max_seats limit
        membership_option = self.active_membership.membership_option
        if membership_option.max_seats:
            current_seats = self.active_membership.seats or 0
            new_total = current_seats + seats_to_add
            max_allowed = int(membership_option.max_seats)

            if new_total > max_allowed:
                raise ValidationError(
                    _(
                        "Cannot add %(add)d seat(s). This would exceed the maximum "
                        "limit of %(max)d seats for this membership option. "
                        "Current seats: %(current)d.",
                    )
                    % {
                        "add": seats_to_add,
                        "max": max_allowed,
                        "current": int(current_seats),
                    },
                    code="exceeds_max_seats",
                )

        return seats_to_add

    def calculate_prorata_cost(self, seats_to_add):
        """
        Calculate the pro-rata cost for additional seats.

        This is a wrapper around the calculate_prorata_seat_cost service function.

        Args:
            seats_to_add: Number of seats to add (int)

        Returns:
            Decimal: Pro-rated cost rounded to 2 decimal places
        """
        return calculate_prorata_seat_cost(self.active_membership, seats_to_add)

    def save(self):
        """
        Process the seat purchase by creating an invoice and updating max_seats.

        Returns:
            tuple: (membership, invoice) where invoice may be None if billing not
                   configured or membership is free

        Raises:
            ValidationError: If billing account or invoice creation fails
        """
        logger = logging.getLogger(__name__)

        seats_to_add = self.cleaned_data["seats_to_add"]
        membership = self.active_membership
        membership_option = membership.membership_option

        # Calculate pro-rata cost
        prorata_cost = self.calculate_prorata_cost(seats_to_add)

        invoice = None

        # Only create invoice if there's a cost
        if prorata_cost > 0:
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

            # Create invoice using membership billing service
            billing_service = MembershipBillingService()
            try:
                # Calculate pro-rata unit price
                unit_price = prorata_cost / Decimal(seats_to_add)

                invoice = billing_service.create_membership_invoice(
                    account,
                    membership_option,
                    seat_count=seats_to_add,
                    membership=membership,
                    unit_price_override=unit_price,
                )
                if invoice:
                    logger.info(
                        "Created invoice %s for additional %d seats for "
                        "organisation %s",
                        invoice.invoice_number,
                        seats_to_add,
                        self.organisation.uuid,
                    )
            except Exception as e:
                logger.exception(
                    "Failed to create invoice for organisation %s",
                    self.organisation.uuid,
                )
                raise ValidationError(
                    _(
                        "Could not create invoice for the seat purchase. "
                        "Please contact us.",
                    ),
                ) from e

        # Update seats immediately (within transaction)
        with transaction.atomic():
            old_seats = membership.seats
            membership.seats = old_seats + Decimal(seats_to_add)
            membership.save(update_fields=["seats"])

            logger.info(
                "Updated seats from %s to %s for membership %s (organisation %s)",
                old_seats,
                membership.seats,
                membership.pk,
                self.organisation.uuid,
            )

        return (membership, invoice)
