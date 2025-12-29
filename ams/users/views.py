from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from ams.memberships.models import MembershipStatus
from ams.users.email_utils import send_organisation_invite_email
from ams.users.forms import InviteOrganisationMemberForm
from ams.users.forms import OrganisationForm
from ams.users.forms import UserUpdateForm
from ams.users.mixins import OrganisationAdminMixin
from ams.users.models import Organisation
from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.tables import MembershipTable
from ams.users.tables import OrganisationMemberTable
from ams.users.tables import OrganisationTable
from ams.users.tables import PendingInvitationTable


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        memberships = user.individual_memberships.all().order_by("-start_date")
        context["membership_table"] = MembershipTable(memberships)
        context["has_memberships"] = memberships.exists()
        context["has_active_membership"] = any(
            m.status() == MembershipStatus.ACTIVE for m in memberships
        )

        # Organizations - separate pending invitations from accepted memberships
        all_org_members = user.organisation_members.select_related(
            "organisation",
        ).prefetch_related("organisation__organisation_memberships")

        # Pending invitations (not yet accepted or declined)
        pending_invitations = all_org_members.filter(
            accepted_datetime__isnull=True,
            declined_datetime__isnull=True,
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


# --- Organisation views ---


class OrganisationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    View for creating a new organisation.
    Upon creation, the current user is added as an organisation admin.
    """

    model = Organisation
    form_class = OrganisationForm
    template_name = "users/organisation_form.html"
    success_message = _("Organisation created successfully")

    def get_success_url(self) -> str:
        return reverse(
            "users:organisation_detail",
            kwargs={"uuid": self.object.uuid},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["cancel_url"] = reverse(
            "users:detail",
            kwargs={"username": self.request.user.username},
        )
        return kwargs

    def form_valid(self, form):
        """
        Save the organisation and add the current user as an organisation admin.
        """
        response = super().form_valid(form)

        # Add the creator as an organisation admin
        OrganisationMember.objects.create(
            user=self.request.user,
            organisation=self.object,
            role=OrganisationMember.Role.ADMIN,
            created_datetime=timezone.now(),
            accepted_datetime=timezone.now(),  # Auto-accept for creator
        )

        return response


organisation_create_view = OrganisationCreateView.as_view()


class OrganisationUpdateView(
    LoginRequiredMixin,
    OrganisationAdminMixin,
    SuccessMessageMixin,
    UpdateView,
):
    """
    View for editing an existing organisation.
    Only staff/admin or organisation admins can edit.
    """

    model = Organisation
    form_class = OrganisationForm
    template_name = "users/organisation_form.html"
    success_message = _("Organisation updated successfully")
    pk_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        """Get organisation by UUID."""
        uuid = self.kwargs.get(self.pk_url_kwarg)
        return Organisation.objects.get(uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organisation = self.get_object()
        kwargs["cancel_url"] = reverse(
            "users:organisation_detail",
            kwargs={"uuid": organisation.uuid},
        )
        return kwargs

    def get_success_url(self) -> str:
        """Redirect to organisation detail page after successful update."""
        return reverse(
            "users:organisation_detail",
            kwargs={"uuid": self.object.uuid},
        )


organisation_update_view = OrganisationUpdateView.as_view()


class OrganisationDetailView(
    LoginRequiredMixin,
    OrganisationAdminMixin,
    DetailView,
):
    """
    View for displaying organisation details and members.
    Only staff/admin or organisation admins can view.
    """

    model = Organisation
    template_name = "users/organisation_detail.html"
    pk_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        """Get organisation by UUID."""
        uuid = self.kwargs.get(self.pk_url_kwarg)
        return Organisation.objects.get(uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.object

        # Get organisation members
        members = organisation.organisation_members.select_related(
            "user",
        ).order_by("-accepted_datetime")
        context["member_table"] = OrganisationMemberTable(members)

        # Get active organisation membership for seats summary

        active_membership = (
            organisation.organisation_memberships.filter(
                cancelled_datetime__isnull=True,
                start_date__lte=timezone.now().date(),
                expiry_date__gte=timezone.now().date(),
            )
            .select_related("membership_option")
            .first()
        )

        if active_membership:
            context["active_membership"] = active_membership
            context["seat_limit"] = (
                int(active_membership.membership_option.max_seats)
                if active_membership.membership_option.max_seats
                else None
            )
            context["occupied_seats"] = active_membership.occupied_seats
        else:
            context["active_membership"] = None
            context["seat_limit"] = None
            context["occupied_seats"] = 0

        return context


organisation_detail_view = OrganisationDetailView.as_view()


class OrganisationInviteMemberView(
    LoginRequiredMixin,
    OrganisationAdminMixin,
    FormView,
):
    """
    View for inviting members to an organisation.
    Only staff/admin or organisation admins can invite members.
    """

    form_class = InviteOrganisationMemberForm
    template_name = "users/organisation_invite_member.html"

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
            "users:organisation_detail",
            kwargs={"uuid": self.organisation.uuid},
        )
        return kwargs

    def get_context_data(self, **kwargs):
        """Add organisation to context."""
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.organisation
        return context

    def form_valid(self, form):
        """Create the invite and send the email."""
        email = form.cleaned_data["email"]

        # Check seat availability and add warning if needed
        active_membership = (
            self.organisation.organisation_memberships.filter(
                cancelled_datetime__isnull=True,
                start_date__lte=timezone.now().date(),
                expiry_date__gte=timezone.now().date(),
            )
            .select_related("membership_option")
            .first()
        )

        if active_membership:
            max_seats = active_membership.membership_option.max_seats
            occupied_seats = active_membership.occupied_seats

            if max_seats and occupied_seats >= int(max_seats):
                # Seats are full - add warning
                messages.warning(
                    self.request,
                    _(
                        "All membership seats are currently occupied. "
                        "The invitee will not be able to accept until a seat "
                        "becomes available.",
                    ),
                )

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        # Create the organisation member invite
        member = OrganisationMember.objects.create(
            organisation=self.organisation,
            user=user,
            invite_email=email,
            created_datetime=timezone.now(),
            role=OrganisationMember.Role.MEMBER,
        )

        # Send invite email using utility function
        send_organisation_invite_email(self.request, member)

        # Add success message
        messages.success(
            self.request,
            _("Invitation sent successfully to %(email)s.") % {"email": email},
        )

        # Redirect to organisation detail
        return redirect(
            reverse(
                "users:organisation_detail",
                kwargs={"uuid": self.organisation.uuid},
            ),
        )


organisation_invite_member_view = OrganisationInviteMemberView.as_view()


class AcceptOrganisationInviteView(LoginRequiredMixin, RedirectView):
    """
    View for accepting an organisation invite.
    User must be logged in and the invite must be for their email.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """Accept the invite and redirect to organisation detail."""
        invite_token = kwargs.get("invite_token")

        # Get the invite
        member = get_object_or_404(
            OrganisationMember,
            invite_token=invite_token,
        )

        # Verify the logged-in user matches the invite
        if member.user and member.user != self.request.user:
            # Invite is for a specific user but logged-in user doesn't match
            messages.error(
                self.request,
                _("This invitation is for a different user."),
            )
            return reverse("users:redirect")

        # For invites sent to non-users (user=None), verify email matches
        if not member.user and member.invite_email:
            if self.request.user.email.lower() != member.invite_email.lower():
                messages.error(
                    self.request,
                    _("This invitation is not valid for your account."),
                )
                return reverse("users:redirect")

        # Check if already accepted
        if member.accepted_datetime:
            # Already accepted, inform user
            messages.info(
                self.request,
                _("You have already accepted this invitation."),
            )
            return reverse(
                "users:organisation_detail",
                kwargs={"uuid": member.organisation.uuid},
            )

        # Check if already declined
        if member.declined_datetime:
            messages.error(
                self.request,
                _("This invitation has been declined and cannot be accepted."),
            )
            return reverse("users:redirect")

        # Check seat availability
        active_membership = (
            member.organisation.organisation_memberships.filter(
                cancelled_datetime__isnull=True,
                start_date__lte=timezone.now().date(),
                expiry_date__gte=timezone.now().date(),
            )
            .select_related("membership_option")
            .first()
        )

        if active_membership:
            max_seats = active_membership.membership_option.max_seats
            occupied_seats = active_membership.occupied_seats

            if max_seats and occupied_seats >= int(max_seats):
                # Seats are full - cannot accept
                messages.error(
                    self.request,
                    _(
                        "Unable to accept invitation: all membership seats are "
                        "currently occupied.",
                    ),
                )
                return reverse(
                    "users:organisation_detail",
                    kwargs={"uuid": member.organisation.uuid},
                )

        # Accept the invite
        member.accepted_datetime = timezone.now()
        if not member.user:
            member.user = self.request.user
        member.save()

        # Add success message
        messages.success(
            self.request,
            _(
                "Welcome! You have successfully joined %(organisation)s.",
            )
            % {"organisation": member.organisation.name},
        )

        # Redirect to organisation detail
        return reverse(
            "users:organisation_detail",
            kwargs={"uuid": member.organisation.uuid},
        )


accept_organisation_invite_view = AcceptOrganisationInviteView.as_view()


class DeclineOrganisationInviteView(LoginRequiredMixin, RedirectView):
    """
    View for declining an organisation invite.
    User must be logged in and the invite must be for their email.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """Decline the invite and redirect to user detail page."""
        invite_token = kwargs.get("invite_token")

        # Get the invite
        member = get_object_or_404(
            OrganisationMember,
            invite_token=invite_token,
        )

        # Verify the logged-in user matches the invite
        if member.user and member.user != self.request.user:
            # Invite is for a specific user but logged-in user doesn't match
            messages.error(
                self.request,
                _("This invitation is for a different user."),
            )
            return reverse("users:redirect")

        # For invites sent to non-users (user=None), verify email matches
        if not member.user and member.invite_email:
            if self.request.user.email.lower() != member.invite_email.lower():
                messages.error(
                    self.request,
                    _("This invitation is not valid for your account."),
                )
                return reverse("users:redirect")

        # Check if already accepted
        if member.accepted_datetime:
            messages.info(
                self.request,
                _("You have already accepted this invitation."),
            )
            return reverse(
                "users:organisation_detail",
                kwargs={"uuid": member.organisation.uuid},
            )

        # Check if already declined
        if member.declined_datetime:
            messages.info(
                self.request,
                _("You have already declined this invitation."),
            )
            return reverse("users:redirect")

        # Decline the invite
        member.declined_datetime = timezone.now()
        if not member.user:
            member.user = self.request.user
        member.save()

        # Add success message
        messages.success(
            self.request,
            _(
                "You have declined the invitation to join %(organisation)s.",
            )
            % {"organisation": member.organisation.name},
        )

        # Redirect to user detail
        return reverse(
            "users:detail",
            kwargs={"username": self.request.user.username},
        )


decline_organisation_invite_view = DeclineOrganisationInviteView.as_view()
