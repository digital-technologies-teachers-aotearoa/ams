from allauth.account.models import EmailAddress
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from ams.memberships.models import OrganisationMembership
from ams.organisations.models import OrganisationMember
from ams.terms.mixins import TermsRequiredMixin
from ams.users.forms import UserUpdateForm
from ams.users.mixins import UserSelfOrStaffMixin
from ams.users.models import ProfileField
from ams.users.models import ProfileFieldResponse
from ams.users.models import User
from ams.users.tables import MembershipTable
from ams.users.tables import OrganisationTable
from ams.users.tables import PendingInvitationTable
from ams.utils.permissions import user_has_active_membership


class UserDetailView(
    LoginRequiredMixin,
    UserSelfOrStaffMixin,
    TermsRequiredMixin,
    DetailView,
):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        memberships = (
            user.individual_memberships.all()
            .prefetch_related("invoices")
            .order_by("-start_date")
        )
        context["membership_table"] = MembershipTable(memberships)
        context["has_memberships"] = memberships.exists()
        context["has_active_membership"] = user_has_active_membership(user)

        # Organizations - separate pending invitations from accepted memberships
        # Query for invites by both user and email to catch invites sent before signup

        # Get all verified email addresses for this user (primary + secondary)
        user_emails = list(
            EmailAddress.objects.filter(
                user=user,
                verified=True,
            ).values_list("email", flat=True),
        )
        # Always include the user's primary email even if not in EmailAddress model
        if user.email and user.email not in user_emails:
            user_emails.append(user.email)

        # Build Q object for case-insensitive email matching
        email_q = Q()
        for email in user_emails:
            email_q |= Q(invite_email__iexact=email)

        # Create subquery for active memberships
        active_membership_subquery = OrganisationMembership.objects.filter(
            organisation=OuterRef("organisation"),
            approved_datetime__isnull=False,
            cancelled_datetime__isnull=True,
            start_date__lte=timezone.localdate(),
            expiry_date__gt=timezone.localdate(),
        )

        all_org_members = (
            OrganisationMember.objects.filter(
                Q(user=user) | email_q,
            )
            .select_related("organisation")
            .annotate(org_has_active_membership=Exists(active_membership_subquery))
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

        # Profile completion tracking
        total_fields = ProfileField.objects.filter(
            is_active=True,
            counts_toward_completion=True,
        ).count()
        if total_fields > 0:
            responses_count = ProfileFieldResponse.objects.filter(
                user=user,
                profile_field__counts_toward_completion=True,
                profile_field__is_active=True,
            ).count()
            context["profile_completion_percentage"] = int(
                (responses_count / total_fields) * 100,
            )
            context["profile_incomplete_count"] = total_fields - responses_count
        else:
            context["profile_completion_percentage"] = 100
            context["profile_incomplete_count"] = 0

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
