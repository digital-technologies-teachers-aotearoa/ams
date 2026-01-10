from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from ams.organisations.models import OrganisationMember
from ams.users.forms import UserUpdateForm
from ams.users.mixins import UserSelfOrStaffMixin
from ams.users.models import User
from ams.users.tables import MembershipTable
from ams.users.tables import OrganisationTable
from ams.users.tables import PendingInvitationTable
from ams.utils.permissions import user_has_active_membership


class UserDetailView(LoginRequiredMixin, UserSelfOrStaffMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        memberships = user.individual_memberships.all().order_by("-start_date")
        context["membership_table"] = MembershipTable(memberships)
        context["has_memberships"] = memberships.exists()
        context["has_active_membership"] = user_has_active_membership(user)

        # Organizations - separate pending invitations from accepted memberships
        # Query for invites by both user and email to catch invites sent before signup

        all_org_members = (
            OrganisationMember.objects.filter(
                Q(user=user) | Q(invite_email__iexact=user.email),
            )
            .select_related(
                "organisation",
            )
            .prefetch_related("organisation__organisation_memberships")
        )

        # Pending invitations (not yet accepted, declined, or revoked)
        pending_invitations = all_org_members.filter(
            accepted_datetime__isnull=True,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        ).order_by("-created_datetime")
        context["pending_invitation_table"] = PendingInvitationTable(
            pending_invitations,
        )
        context["has_pending_invitations"] = pending_invitations.exists()

        # Accepted organisations
        accepted_organisations = all_org_members.filter(
            accepted_datetime__isnull=False,
        ).order_by("-accepted_datetime")
        context["organisation_table"] = OrganisationTable(accepted_organisations)
        context["has_organisations"] = accepted_organisations.exists()

        return context


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    success_message = _("Your user details have been successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
