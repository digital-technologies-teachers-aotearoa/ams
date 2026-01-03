from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from ams.memberships.forms import CreateIndividualMembershipForm
from ams.memberships.forms import CreateOrganisationMembershipForm
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.organisations.email_utils import (
    send_staff_organisation_membership_notification,
)
from ams.organisations.mixins import OrganisationAdminMixin
from ams.organisations.models import Organisation


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


class CreateOrganisationMembershipView(
    LoginRequiredMixin,
    OrganisationAdminMixin,
    FormView,
):
    """
    View for adding a membership to an organisation.
    Only staff/admin or organisation admins can add memberships.
    """

    form_class = CreateOrganisationMembershipForm
    template_name = "organisations/organisation_add_membership.html"

    def dispatch(self, request, *args, **kwargs):
        """Store the organisation for use in get_form_kwargs and form_valid."""
        self.organisation = get_object_or_404(Organisation, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        """Required by OrganisationAdminMixin."""
        return self.organisation

    def get_form_kwargs(self):
        """Pass organisation and cancel_url to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.organisation
        kwargs["cancel_url"] = reverse(
            "organisations:detail",
            kwargs={"uuid": self.organisation.uuid},
        )
        return kwargs

    def get_context_data(self, **kwargs):
        """Add organisation and membership data to context."""
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.organisation

        # Build membership data for JavaScript calculations
        membership_data = {}
        for option in MembershipOption.objects.filter(
            type=MembershipOptionType.ORGANISATION,
            archived=False,
        ):
            # Decompose duration for JS
            years = getattr(option.duration, "years", 0) or 0
            months = getattr(option.duration, "months", 0) or 0
            weeks = 0
            days = getattr(option.duration, "days", 0) or 0
            if days and days % 7 == 0:
                weeks = days // 7
                days = 0

            membership_data[str(option.id)] = {
                "years": years,
                "months": months,
                "weeks": weeks,
                "days": days,
                "cost": float(option.cost),
                "max_seats": int(option.max_seats) if option.max_seats else None,
            }

        context["membership_data_json"] = membership_data
        return context

    def form_valid(self, form):
        """Create the membership and redirect with success message."""
        # Save the form (creates membership and invoice)
        membership = form.save()

        # Send staff notification
        send_staff_organisation_membership_notification(membership)

        # Add success message
        messages.success(
            self.request,
            _(
                "Membership added successfully. "
                "%(seats)s seats available until %(expiry)s.",
            )
            % {
                "seats": membership.max_seats,
                "expiry": membership.expiry_date.strftime("%d/%m/%Y"),
            },
        )

        # Redirect to organisation detail
        return redirect(
            reverse(
                "organisations:detail",
                kwargs={"uuid": self.organisation.uuid},
            ),
        )


add_organisation_membership_view = CreateOrganisationMembershipView.as_view()
