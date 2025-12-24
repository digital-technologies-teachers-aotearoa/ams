import logging
from typing import Any

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
        # Use the provided start_date from the form
        instance.expiry_date = instance.start_date + instance.membership_option.duration
        instance.created_datetime = timezone.now()

        membership_option = instance.membership_option
        if membership_option.cost and membership_option.cost > 0:
            try:
                account, created = Account.objects.get_or_create(user=user)
            except Exception as e:
                logger.exception(
                    "Failed to get or create billing account for user %s",
                    user.username,
                )
                raise ValidationError(
                    _("Could not create billing account. Please contact us."),
                ) from e

            try:
                billing_service = MembershipBillingService()
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
