from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from ams.memberships.forms import CreateIndividualMembershipForm
from ams.memberships.models import MembershipOption


class CreateIndividualMembershipView(LoginRequiredMixin, FormView):
    """Allow an authenticated user to apply for an individual membership.

    Presents a form of available individual membership options. On success it
    creates an IndividualMembership for the current user (pending approval).
    """

    template_name = "memberships/apply_individual.html"
    form_class = CreateIndividualMembershipForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):  # type: ignore[override]
        return reverse("users:detail", args=[self.request.user.username])

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
        membership_durations = {}
        for option in MembershipOption.objects.filter(type="INDIVIDUAL"):
            # Decompose duration for JS
            years = getattr(option.duration, "years", 0) or 0
            months = getattr(option.duration, "months", 0) or 0
            weeks = 0
            days = getattr(option.duration, "days", 0) or 0
            if days and days % 7 == 0:
                weeks = days // 7
                days = 0
            membership_durations[str(option.id)] = {
                "years": years,
                "months": months,
                "weeks": weeks,
                "days": days,
            }
        ctx["membership_durations_json"] = membership_durations
        return ctx
