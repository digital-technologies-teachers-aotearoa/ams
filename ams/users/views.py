from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from ams.memberships.models import MembershipStatus
from ams.users.forms import OrganisationForm
from ams.users.forms import UserUpdateForm
from ams.users.models import Organisation
from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.tables import MembershipTable
from ams.users.tables import OrganisationTable


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

        # Organizations
        organisations = (
            user.organisation_members.select_related("organisation")
            .prefetch_related("organisation__organisation_memberships")
            .order_by("-accepted_datetime")
        )
        context["organisation_table"] = OrganisationTable(organisations)
        context["has_organisations"] = organisations.exists()

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
        return reverse("users:detail", kwargs={"username": self.request.user.username})

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


class OrganisationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
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
        kwargs["cancel_url"] = reverse(
            "users:detail",
            kwargs={"username": self.request.user.username},
        )
        return kwargs

    def get_success_url(self) -> str:
        """Redirect to home page after successful update."""
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def dispatch(self, request, *args, **kwargs):
        """
        Check permissions before allowing access.
        Only staff/admin or organisation admins can edit.
        """
        organisation = self.get_object()

        # Allow staff/admin
        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Check if user is an organisation admin
        is_org_admin = OrganisationMember.objects.filter(
            organisation=organisation,
            user=request.user,
            role=OrganisationMember.Role.ADMIN,
        ).exists()

        if is_org_admin:
            return super().dispatch(request, *args, **kwargs)

        # Deny access
        messages.error(
            request,
            _("You do not have permission to edit this organisation."),
        )
        return redirect("root_redirect")


organisation_update_view = OrganisationUpdateView.as_view()
