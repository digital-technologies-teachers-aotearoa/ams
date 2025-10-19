from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from ams.memberships.constants import MEMBERSHIP_DATE_DISPLAY_FORMAT
from ams.memberships.forms import CreateIndividualMembershipForm
from ams.memberships.models import MembershipOption


class CreateIndividualMembershipView(LoginRequiredMixin, FormView):
    """Allow an authenticated user to apply for an individual membership.

    Presents a form of available individual membership options. On success it
    creates an IndividualMembership for the current user (pending approval).
    """

    template_name = "memberships/apply_individual.html"
    form_class = CreateIndividualMembershipForm

    def get_success_url(self):  # type: ignore[override]
        return reverse("users:detail", args=[self.request.user.pk])

    def form_valid(self, form):  # type: ignore[override]
        form.save(user=self.request.user)
        messages.success(
            self.request,
            _(
                "Your membership application has been submitted.",
            ),
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        ctx = super().get_context_data(**kwargs)
        start_date = timezone.localdate()
        # Locale-aware formatting using Django's date_format utility.
        # Use 'DATE_FORMAT' (respects current locale / LANGUAGE_CODE).
        start_date_display = date_format(
            start_date,
            format=MEMBERSHIP_DATE_DISPLAY_FORMAT,
        )
        # Build mapping of membership option id -> formatted end/expiry date
        option_end_dates: dict[int, str] = {}
        for option in MembershipOption.objects.filter(type="INDIVIDUAL"):
            end_date = start_date + option.duration
            option_end_dates[option.id] = date_format(
                end_date,
                format=MEMBERSHIP_DATE_DISPLAY_FORMAT,
            )
        ctx["start_date"] = start_date  # raw date (if needed elsewhere)
        ctx["start_date_display"] = start_date_display
        ctx["option_end_dates"] = option_end_dates
        return ctx
