from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from ams.organisations.email_utils import send_organisation_invite_email
from ams.organisations.email_utils import send_staff_organisation_created_notification
from ams.organisations.forms import InviteOrganisationMemberForm
from ams.organisations.forms import OrganisationForm
from ams.organisations.mixins import OrganisationAdminMixin
from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember
from ams.organisations.tables import OrganisationMembershipTable
from ams.organisations.tables import OrganisationMemberTable
from ams.users.models import User


class OrganisationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    View for creating a new organisation.
    Upon creation, the current user is added as an organisation admin.
    """

    model = Organisation
    form_class = OrganisationForm
    template_name = "organisations/organisation_form.html"
    success_message = _("Organisation created successfully")

    def get_success_url(self) -> str:
        return reverse(
            "organisations:detail",
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

        # Send staff notification
        send_staff_organisation_created_notification(self.object, self.request.user)

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
    template_name = "organisations/organisation_form.html"
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
            "organisations:detail",
            kwargs={"uuid": organisation.uuid},
        )
        return kwargs

    def get_success_url(self) -> str:
        """Redirect to organisation detail page after successful update."""
        return reverse(
            "organisations:detail",
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
    template_name = "organisations/organisation_detail.html"
    pk_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        """Get organisation by UUID."""
        uuid = self.kwargs.get(self.pk_url_kwarg)
        return Organisation.objects.get(uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.object

        # Get organisation members (exclude declined and revoked invites)
        members = (
            organisation.organisation_members.filter(
                declined_datetime__isnull=True,
                revoked_datetime__isnull=True,
            )
            .select_related(
                "user",
            )
            .order_by("-accepted_datetime")
        )
        context["member_table"] = OrganisationMemberTable(
            members,
            request=self.request,
            organisation=organisation,
        )

        # Get organisation memberships
        memberships = organisation.organisation_memberships.select_related(
            "membership_option",
            "invoice",
        ).order_by("-start_date")
        context["membership_table"] = OrganisationMembershipTable(memberships)

        # Get active organisation membership for seats summary
        active_membership = (
            organisation.organisation_memberships.active()
            .select_related("membership_option")
            .first()
        )

        if active_membership:
            context["active_membership"] = active_membership
            context["seats"] = int(active_membership.seats)
            context["occupied_seats"] = active_membership.occupied_seats
            context["membership_seat_limit"] = (
                active_membership.membership_option.max_seats
            )
        else:
            context["active_membership"] = None
            context["seats"] = None
            context["occupied_seats"] = 0
            context["membership_seat_limit"] = None

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
    template_name = "organisations/organisation_invite_member.html"

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
        """Add organisation to context."""
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.organisation
        return context

    def form_valid(self, form):
        """Create the invite and send the email."""
        email = form.cleaned_data["email"]

        # Check seat availability and add warning if needed
        active_membership = (
            self.organisation.organisation_memberships.active()
            .select_related("membership_option")
            .first()
        )

        if active_membership and active_membership.is_full:
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
        # Note: Partial unique constraint allows multiple declined invites
        # but only one active/pending invite per user+organisation
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
                "organisations:detail",
                kwargs={"uuid": self.organisation.uuid},
            ),
        )


organisation_invite_member_view = OrganisationInviteMemberView.as_view()


def _validate_invite(member, request, action: str):  # noqa: PLR0911
    """
    Validate whether the invite can be accepted or declined.

    Returns:
        None if valid
        (message, level, redirect_url) otherwise
    """
    redirect_url = reverse("users:redirect")
    user_detail_url = reverse(
        "users:detail",
        kwargs={"username": request.user.username},
    )
    organisation_detail_url = reverse(
        "organisations:detail",
        kwargs={"uuid": member.organisation.uuid},
    )

    # Ownership / email validation (shared logic)
    if member.user and member.user != request.user:
        return (
            _("This invitation is for a different user."),
            messages.ERROR,
            redirect_url,
        )

    if not member.user and member.invite_email:
        if request.user.email.lower() != member.invite_email.lower():
            return (
                _("This invitation is not valid for your account."),
                messages.ERROR,
                redirect_url,
            )

    # Revoked (shared logic)
    if member.revoked_datetime:
        message = (
            _("This invitation has been revoked and can no longer be accepted.")
            if action == "accept"
            else _("This invitation has been revoked and can no longer be declined.")
        )
        return (message, messages.ERROR, redirect_url)

    # Already accepted
    if member.accepted_datetime:
        message = _("You have already accepted this invitation.")
        return (
            message,
            messages.INFO,
            organisation_detail_url if action == "decline" else user_detail_url,
        )

    # Already declined
    if member.declined_datetime:
        message = (
            _("You have already declined this invitation.")
            if action == "decline"
            else _("This invitation has been declined and cannot be accepted.")
        )
        return (
            message,
            messages.INFO if action == "decline" else messages.ERROR,
            redirect_url,
        )

    # Accept-specific validation
    if action == "accept":
        active_membership = (
            member.organisation.organisation_memberships.active()
            .select_related("membership_option")
            .first()
        )

        if active_membership and active_membership.is_full:
            return (
                _(
                    "Unable to accept invitation: all membership seats are "
                    "currently occupied.",
                ),
                messages.ERROR,
                user_detail_url,
            )

    return None


class AcceptOrganisationInviteView(LoginRequiredMixin, RedirectView):
    """
    View for accepting an organisation invite.
    User must be logged in and the invite must be for their email.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        invite_token = kwargs.get("invite_token")

        member = get_object_or_404(
            OrganisationMember,
            invite_token=invite_token,
        )

        validation_result = _validate_invite(member, self.request, action="accept")

        if validation_result:
            message, level, redirect_url = validation_result
            messages.add_message(self.request, level, message)
            return redirect_url

        # Accept the invite
        member.accepted_datetime = timezone.now()
        if not member.user:
            member.user = self.request.user
        member.save()

        messages.success(
            self.request,
            _(
                "Welcome! You have successfully joined %(organisation)s.",
            )
            % {"organisation": member.organisation.name},
        )

        return reverse(
            "users:detail",
            kwargs={"username": self.request.user.username},
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

        validation_result = _validate_invite(member, self.request, action="decline")

        if validation_result:
            message, level, redirect_url = validation_result
            messages.add_message(self.request, level, message)
            return redirect_url

        # Decline the invite
        member.declined_datetime = timezone.now()
        if not member.user:
            member.user = self.request.user
        member.save()

        messages.success(
            self.request,
            _(
                "You have declined the invitation to join %(organisation)s.",
            )
            % {"organisation": member.organisation.name},
        )

        return reverse(
            "users:detail",
            kwargs={"username": self.request.user.username},
        )


decline_organisation_invite_view = DeclineOrganisationInviteView.as_view()


class RemoveOrganisationMemberView(LoginRequiredMixin, OrganisationAdminMixin, View):
    """
    View for removing a member from an organisation.
    Only staff/admin or organisation admins can remove members.
    Admins cannot remove themselves (use LeaveOrganisationView instead).
    Ensures at least one admin remains in the organisation.
    """

    def get_object(self):
        """Get the organisation by UUID for permission checking."""
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(Organisation, uuid=uuid)

    def post(self, request, *args, **kwargs):
        """Remove the specified member from the organisation."""
        organisation = self.get_object()
        member_uuid = kwargs.get("member_uuid")

        # Get the member to remove
        member = get_object_or_404(
            OrganisationMember,
            uuid=member_uuid,
            organisation=organisation,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        )

        # Prevent removing yourself through this action
        if member.user == request.user:
            return HttpResponseBadRequest(
                "Cannot remove yourself. Use the Leave Organisation action instead.",
            )

        # If removing an admin, ensure at least one admin will remain
        if member.role == OrganisationMember.Role.ADMIN:
            admin_count = OrganisationMember.objects.filter(
                organisation=organisation,
                role=OrganisationMember.Role.ADMIN,
                declined_datetime__isnull=True,
                revoked_datetime__isnull=True,
            ).count()

            if admin_count <= 1:
                messages.error(
                    request,
                    _(
                        "Cannot remove the last admin. "
                        "Please promote another member to admin first.",
                    ),
                )
                return redirect(
                    reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
                )

        # Remove the member
        member_name = member.user.get_full_name()
        member.delete()

        messages.success(
            request,
            _("Successfully removed %(name)s from the organisation.")
            % {"name": member_name},
        )

        return redirect(
            reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
        )


remove_organisation_member_view = RemoveOrganisationMemberView.as_view()


class MakeOrganisationAdminView(LoginRequiredMixin, OrganisationAdminMixin, View):
    """
    View for promoting a member to admin role.
    Only staff/admin or organisation admins can promote members.
    Can only promote active members (not pending invites).
    Admins cannot promote themselves (they're already admins).
    """

    def get_object(self):
        """Get the organisation by UUID for permission checking."""
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(Organisation, uuid=uuid)

    def post(self, request, *args, **kwargs):
        """Promote the specified member to admin role."""
        organisation = self.get_object()
        member_uuid = kwargs.get("member_uuid")

        # Get the member to promote
        member = get_object_or_404(
            OrganisationMember,
            uuid=member_uuid,
            organisation=organisation,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        )

        # Validate that the member is active (not a pending invite)
        if not member.is_active():
            return HttpResponseBadRequest(
                "Only active members can be promoted to admin.",
            )

        # Check if already an admin
        if member.role == OrganisationMember.Role.ADMIN:
            messages.info(
                request,
                _("%(name)s is already an admin.")
                % {"name": member.user.get_full_name()},
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Promote to admin
        member.role = OrganisationMember.Role.ADMIN
        member.save()

        messages.success(
            request,
            _("Successfully promoted %(name)s to admin.")
            % {"name": member.user.get_full_name()},
        )

        return redirect(
            reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
        )


make_organisation_admin_view = MakeOrganisationAdminView.as_view()


class RevokeOrganisationAdminView(LoginRequiredMixin, OrganisationAdminMixin, View):
    """
    View for revoking admin role from a member.
    Only staff/admin or organisation admins can revoke admin status.
    Admins cannot revoke their own admin status.
    Ensures at least one admin remains in the organisation.
    """

    def get_object(self):
        """Get the organisation by UUID for permission checking."""
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(Organisation, uuid=uuid)

    def post(self, request, *args, **kwargs):
        """Revoke admin role from the specified member."""
        organisation = self.get_object()
        member_uuid = kwargs.get("member_uuid")

        # Get the member to demote
        member = get_object_or_404(
            OrganisationMember,
            uuid=member_uuid,
            organisation=organisation,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        )

        # Prevent revoking yourself through this action
        if member.user == request.user:
            return HttpResponseBadRequest(
                "Cannot revoke your own admin status. "
                "Use the Leave Organisation action if you want to leave.",
            )

        # Check if already a regular member
        if member.role == OrganisationMember.Role.MEMBER:
            messages.info(
                request,
                _("%(name)s is already a regular member.")
                % {"name": member.user.get_full_name()},
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Ensure at least one admin will remain
        admin_count = OrganisationMember.objects.filter(
            organisation=organisation,
            role=OrganisationMember.Role.ADMIN,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        ).count()

        if admin_count <= 1:
            messages.error(
                request,
                _(
                    "Cannot revoke admin status from the last admin. "
                    "Please promote another member to admin first.",
                ),
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Revoke admin status
        member.role = OrganisationMember.Role.MEMBER
        member.save()

        messages.success(
            request,
            _("Successfully revoked admin status from %(name)s.")
            % {"name": member.user.get_full_name()},
        )

        return redirect(
            reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
        )


revoke_organisation_admin_view = RevokeOrganisationAdminView.as_view()


class LeaveOrganisationView(LoginRequiredMixin, View):
    """
    View for leaving an organisation (removing yourself as a member).
    Any member can leave an organisation.
    If you're an admin, ensures at least one admin remains.
    """

    def post(self, request, *args, **kwargs):
        """Remove the current user from the organisation."""
        uuid = kwargs.get("uuid")
        organisation = get_object_or_404(Organisation, uuid=uuid)

        # Get the current user's membership
        try:
            member = OrganisationMember.objects.get(
                organisation=organisation,
                user=request.user,
                declined_datetime__isnull=True,
                revoked_datetime__isnull=True,
            )
        except OrganisationMember.DoesNotExist:
            return HttpResponseBadRequest("You are not a member of this organisation.")

        # If user is an admin, ensure at least one admin will remain
        if member.role == OrganisationMember.Role.ADMIN:
            admin_count = OrganisationMember.objects.filter(
                organisation=organisation,
                role=OrganisationMember.Role.ADMIN,
                declined_datetime__isnull=True,
                revoked_datetime__isnull=True,
            ).count()

            if admin_count <= 1:
                messages.error(
                    request,
                    _(
                        "You are the last admin of this organisation. "
                        "Please promote another member to admin before leaving.",
                    ),
                )
                return redirect(
                    reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
                )

        # Remove the member
        member.delete()

        messages.success(
            request,
            _("You have successfully left %(organisation)s.")
            % {"organisation": organisation.name},
        )

        # Redirect to user detail page
        return redirect(
            reverse("users:detail", kwargs={"username": request.user.username}),
        )


leave_organisation_view = LeaveOrganisationView.as_view()


class DeactivateOrganisationView(LoginRequiredMixin, OrganisationAdminMixin, View):
    """
    View for deactivating an organisation.
    Only staff/admin or organisation admins can deactivate.
    The organisation must contain only the requesting user as a member.
    """

    def get_object(self):
        """Get the organisation by UUID for permission checking."""
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(Organisation, uuid=uuid)

    def post(self, request, *args, **kwargs):
        """Deactivate the organisation if the user is the only member."""
        organisation = self.get_object()

        # Get all active members (not declined or revoked)
        active_members = OrganisationMember.objects.filter(
            organisation=organisation,
            declined_datetime__isnull=True,
            revoked_datetime__isnull=True,
        )

        # Check if there is exactly one member
        if active_members.count() != 1:
            messages.error(
                request,
                _(
                    "Cannot deactivate organisation with multiple members. "
                    "You must be the only member to deactivate this organisation.",
                ),
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Check if the only member is the requesting user
        only_member = active_members.first()
        if only_member.user != request.user:
            messages.error(
                request,
                _(
                    "You are not a member of this organisation and "
                    "cannot deactivate it.",
                ),
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Store organisation name for success message
        org_name = organisation.name

        # Deactivate the organisation (will auto-cancel memberships and revoke invites)
        organisation.is_active = False
        organisation.save()

        messages.success(
            request,
            _("Successfully deactivated %(organisation)s.")
            % {"organisation": org_name},
        )

        # Redirect to user detail page
        return redirect(
            reverse("users:detail", kwargs={"username": request.user.username}),
        )


deactivate_organisation_view = DeactivateOrganisationView.as_view()


class RevokeOrganisationInviteView(LoginRequiredMixin, OrganisationAdminMixin, View):
    """
    View for revoking a pending organisation invite.
    Only staff/admin or organisation admins can revoke invites.
    Can only revoke invites that haven't been accepted, declined, or already revoked.
    """

    def get_object(self):
        """Get the organisation by UUID for permission checking."""
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(Organisation, uuid=uuid)

    def post(self, request, *args, **kwargs):
        """Revoke the specified invite."""
        organisation = self.get_object()
        member_uuid = kwargs.get("member_uuid")

        # Get the member invite
        member = get_object_or_404(
            OrganisationMember,
            uuid=member_uuid,
            organisation=organisation,
        )

        # Check if already accepted
        if member.accepted_datetime:
            messages.error(
                request,
                _("Cannot revoke an invite that has already been accepted."),
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Check if already declined
        if member.declined_datetime:
            messages.error(
                request,
                _("Cannot revoke an invite that has already been declined."),
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Check if already revoked
        if member.revoked_datetime:
            messages.info(
                request,
                _("This invite has already been revoked."),
            )
            return redirect(
                reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
            )

        # Revoke the invite
        member.revoked_datetime = timezone.now()
        member.save()

        messages.success(
            request,
            _("Successfully revoked invite to %(email)s.")
            % {"email": member.invite_email or member.user.email},
        )

        return redirect(
            reverse("organisations:detail", kwargs={"uuid": organisation.uuid}),
        )


revoke_organisation_invite_view = RevokeOrganisationInviteView.as_view()
