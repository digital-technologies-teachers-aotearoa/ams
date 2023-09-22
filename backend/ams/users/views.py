from functools import partial
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import QuerySet
from django.forms import BoundField
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django_tables2 import SingleTableMixin, SingleTableView
from os import environ
from pydiscourse.sso import sso_validate, sso_redirect_url
from registration.models import RegistrationProfile

from ..base.models import EmailConfirmationPage
from .forms import (
    AddUserMembershipForm,
    EditUserProfileForm,
    IndividualRegistrationForm,
    MembershipOptionForm,
    OrganisationForm,
)
from .models import MembershipOption, Organisation, UserMembership, UserMemberStatus
from .tables import (
    AdminMembershipOptionTable,
    AdminOrganisationTable,
    AdminUserDetailMembershipTable,
    AdminUserMembershipTable,
    AdminUserTable,
    UserDetailMembershipTable,
)
from .utils import UserIsAdminMixin, user_is_admin


def individual_registration(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = IndividualRegistrationForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            # Create a new user using their email as the username and send activation email
            new_user = RegistrationProfile.objects.create_inactive_user(
                get_current_site(request),
                send_email=True,
                username=form_data["email"],
                email=form_data["email"],
                first_name=form_data["first_name"],
                last_name=form_data["last_name"],
                password=form_data["password"],
            )

            membership_option = MembershipOption.objects.get(name=form_data["membership_option"])
            UserMembership.objects.create(
                user=new_user,
                membership_option=membership_option,
                start_date=timezone.localdate(),
                created_datetime=timezone.localtime(),
            )

            return render(
                request,
                "individual_registration_pending.html",
                status=201,
            )
    else:
        form = IndividualRegistrationForm()

    personal_detail_fields = []
    membership_option_field: Optional[BoundField] = None

    for field in form:
        if field.name == "membership_option":
            membership_option_field = field
        else:
            personal_detail_fields.append(field)

    return render(
        request,
        "individual_registration.html",
        {
            "form": form,
            "personal_detail_fields": personal_detail_fields,
            "membership_option_field": membership_option_field,
        },
    )


@login_required
def create_organisation(request: HttpRequest) -> HttpResponse:
    if not user_is_admin(request):
        return HttpResponse(status=403)

    if request.method == "POST":
        form = OrganisationForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            # Create a new user using their email as the username and send activation email
            Organisation.objects.create(
                type=form_data["type"],
                name=form_data["name"],
                postal_address=form_data["postal_address"],
                office_phone=form_data["office_phone"],
            )

            admin_organisations_url = reverse("admin-organisations")
            return HttpResponseRedirect(admin_organisations_url + "?organisation_created=true")
    else:
        form = OrganisationForm()

    return render(
        request,
        "create_organisation.html",
        {
            "form": form,
        },
    )


def notify_staff_of_new_user(request: HttpRequest, new_user: User) -> HttpResponse:
    site = get_current_site(request)
    from_email = settings.DEFAULT_FROM_EMAIL

    staff_users = User.objects.filter(is_staff=True, is_active=True)
    for user in staff_users:
        subject = _("New user registration")
        template = "new_user_email.txt"
        context = {
            "user": user,
            "new_user": new_user,
            "site": site,
        }

        message = render_to_string(template, context, request=request)

        send_mail(subject, message, from_email, [user.email])


def activate_user(request: HttpRequest, activation_key: str) -> HttpResponse:
    user, activation_successful = RegistrationProfile.objects.activate_user(activation_key, get_current_site(request))

    if user:
        if activation_successful:
            transaction.on_commit(partial(notify_staff_of_new_user, request=request, new_user=user))

            email_confirmation_page = EmailConfirmationPage.objects.get(
                live=True, locale__language_code=settings.LANGUAGE_CODE
            )
            return email_confirmation_page.serve(request)
        elif user.is_active:
            return HttpResponseRedirect("/")

    return HttpResponse(status=401)


@login_required
def edit_user_profile(request: HttpRequest, pk: int) -> HttpResponse:
    if not (user_is_admin(request) or request.user.pk == pk):
        return HttpResponse(status=401)

    user = User.objects.get(pk=pk)

    if user_is_admin(request):
        user_view_url = reverse("admin-user-view", kwargs={"pk": pk})
    else:
        user_view_url = reverse("current-user-view")

    if request.method == "POST":
        form = EditUserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(user_view_url + "?profile_updated=true")
    else:
        form = EditUserProfileForm(instance=user)

    return render(
        request,
        "edit_user_profile.html",
        {
            "user_view_url": user_view_url,
            "form": form,
        },
    )


def notify_staff_of_new_user_membership(request: HttpRequest, user_membership: UserMembership) -> HttpResponse:
    site = get_current_site(request)
    from_email = settings.DEFAULT_FROM_EMAIL

    staff_users = User.objects.filter(is_staff=True, is_active=True)
    for user in staff_users:
        subject = _("New user membership")
        template = "new_user_membership_email.txt"
        context = {
            "user": user,
            "user_membership": user_membership,
            "site": site,
        }

        message = render_to_string(template, context, request=request)

        send_mail(subject, message, from_email, [user.email])


@login_required
def add_user_membership(request: HttpRequest, pk: int) -> HttpResponse:
    if not (user_is_admin(request) or request.user.pk == pk):
        return HttpResponse(status=401)

    user = User.objects.get(pk=pk)
    current_membership = user.get_current_membership()

    if user_is_admin(request):
        user_view_url = reverse("admin-user-view", kwargs={"pk": pk})
    else:
        user_view_url = reverse("current-user-view")

    if request.method == "POST":
        form = AddUserMembershipForm(request.POST, user=user)
        if form.is_valid():
            form_data = form.cleaned_data

            start_date = form_data["start_date"]
            membership_option = MembershipOption.objects.get(name=form_data["membership_option"])

            user_membership = UserMembership.objects.create(
                user=user,
                membership_option=membership_option,
                start_date=start_date,
                created_datetime=timezone.localtime(),
            )

            transaction.on_commit(
                partial(notify_staff_of_new_user_membership, request=request, user_membership=user_membership)
            )

            return HttpResponseRedirect(user_view_url + "?membership_added=true")
    else:
        start_date = timezone.localdate()

        if current_membership:
            membership_expiry_date = current_membership.expiry_date()

            if membership_expiry_date > timezone.localdate():
                start_date = membership_expiry_date

        initial_values = {"start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT)}

        form = AddUserMembershipForm(initial=initial_values, user=user)

    return render(
        request,
        "add_user_membership.html",
        {
            "user_view_url": user_view_url,
            "current_membership": current_membership,
            "user_detail": user,
            "form": form,
        },
    )


@login_required
def create_membership_option(request: HttpRequest) -> HttpResponse:
    if not user_is_admin(request):
        return HttpResponse(status=401)

    if request.method == "POST":
        form = MembershipOptionForm(request.POST)
        if form.is_valid():
            form.save()
            membership_options_url = reverse("admin-membership-options")
            return HttpResponseRedirect(membership_options_url + "?membership_option_created=true")
    else:
        form = MembershipOptionForm()

    return render(
        request,
        "edit_membership_option.html",
        {
            "membership_option": None,
            "form": form,
        },
    )


@login_required
def edit_membership_option(request: HttpRequest, pk: int) -> HttpResponse:
    if not user_is_admin(request):
        return HttpResponse(status=401)

    membership_option = MembershipOption.objects.get(pk=pk)

    if request.method == "POST":
        form = MembershipOptionForm(request.POST, instance=membership_option)
        if form.is_valid():
            form.save()
            membership_options_url = reverse("admin-membership-options")
            return HttpResponseRedirect(membership_options_url + "?membership_option_updated=true")
    else:
        form = MembershipOptionForm(instance=membership_option)

    return render(
        request,
        "edit_membership_option.html",
        {
            "membership_option": membership_option,
            "form": form,
        },
    )

@login_required
def discourse_sso(request: HttpRequest) -> HttpResponse:
    secret = environ.get("DISCOURSE_CONNECT_SECRET")

    payload = request.GET.get('sso')
    signature = request.GET.get('sig')

    nonce = sso_validate(payload, signature, secret)

    url = sso_redirect_url(nonce, secret, request.user.email, request.user.id, request.user.username)

    return HttpResponseRedirect(environ.get("DISCOURSE_REDIRECT_DOMAIN") + url)


class AdminUserListView(UserIsAdminMixin, SingleTableView):
    model = User
    table_class = AdminUserTable
    template_name = "admin_user_list.html"


def approve_user_membership(user_membership_id: int) -> HttpResponse:
    user_membership = UserMembership.objects.get(pk=user_membership_id)

    if not user_membership.approved_datetime and not user_membership.cancelled_datetime:
        user_membership.approved_datetime = timezone.now()
        user_membership.save()
        return True

    return False


def cancel_user_membership(user_membership_id: int) -> HttpResponse:
    user_membership = UserMembership.objects.get(pk=user_membership_id)

    if not user_membership.cancelled_datetime and not user_membership.is_expired():
        user_membership.cancelled_datetime = timezone.now()
        user_membership.save()
        return True

    return False


class MembershipActionMixin:
    def membership_post_action(self, request: HttpRequest, redirect_url: str) -> HttpResponse:
        if request.POST.get("action") == "approve_user_membership":
            try:
                user_membership_id = int(request.POST["user_membership_id"])
                if approve_user_membership(user_membership_id):
                    redirect_url += "?membership_approved=true"

                return HttpResponseRedirect(redirect_url)

            except Exception:
                return HttpResponse(status=400)

        elif request.POST.get("action") == "cancel_user_membership":
            try:
                user_membership_id = int(request.POST["user_membership_id"])
                if cancel_user_membership(user_membership_id):
                    redirect_url += "?membership_cancelled=true"

                return HttpResponseRedirect(redirect_url)

            except Exception:
                return HttpResponse(status=400)

        return HttpResponse(status=400)

    def membership_action_context(self, request: HttpRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        if request.method == "GET" and request.GET.get("membership_cancelled"):
            context["show_messages"] = [_("Membership Cancelled")]

        if request.method == "GET" and request.GET.get("membership_approved"):
            context["show_messages"] = [_("Membership Approved")]

        return context


class AdminUserMembershipListView(UserIsAdminMixin, SingleTableView, MembershipActionMixin):
    model = UserMembership
    table_class = AdminUserMembershipTable
    template_name = "admin_user_memberships.html"

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        redirect_url = reverse("admin-user-memberships")
        return self.membership_post_action(request, redirect_url)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        return self.membership_action_context(self.request, context)


class AdminMembershipOptionListView(UserIsAdminMixin, SingleTableView):
    model = MembershipOption
    table_class = AdminMembershipOptionTable
    template_name = "admin_membership_options.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if self.request.method == "GET" and self.request.GET.get("membership_option_created"):
            context["show_messages"] = [_("Membership Option Added")]

        if self.request.method == "GET" and self.request.GET.get("membership_option_updated"):
            context["show_messages"] = [_("Membership Option Saved")]

        return context


class UserDetailViewBase(SingleTableMixin, DetailView):
    model = User
    template_name = "user_view.html"
    context_object_name = "user_detail"

    def get_table_data(self) -> QuerySet:
        return self.object.user_memberships.all()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        user = context["user_detail"]

        latest_membership = user.get_latest_membership()
        can_add_membership = False
        if not latest_membership or latest_membership.status() in [UserMemberStatus.ACTIVE, UserMemberStatus.EXPIRED]:
            can_add_membership = True

        context["can_add_membership"] = can_add_membership

        if self.request.method == "GET" and self.request.GET.get("profile_updated"):
            context["show_messages"] = [_("Profile Updated")]
        return context


class UserDetailView(LoginRequiredMixin, UserDetailViewBase):
    table_class = UserDetailMembershipTable

    def get_object(self) -> User:
        return User.objects.get(id=self.request.user.pk)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if user_is_admin(request):
            # Redirect to admin user view
            return HttpResponseRedirect(f"/users/view/{request.user.pk}/")
        return super().get(request, args, kwargs)


class AdminUserDetailView(UserIsAdminMixin, UserDetailViewBase, MembershipActionMixin):
    table_class = AdminUserDetailMembershipTable

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        redirect_url = reverse("admin-user-view", kwargs={"pk": self.object.pk})
        return self.membership_post_action(request, redirect_url)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        return self.membership_action_context(self.request, context)


class AdminOrganisationListView(UserIsAdminMixin, SingleTableView):
    model = Organisation
    table_class = AdminOrganisationTable
    template_name = "admin_organisations.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        referrer_url = self.request.META.get("HTTP_REFERER")

        if referrer_url:
            # Show message when returning from creating an organisation
            admin_create_organisation_url = reverse("admin-create-organisation")
            if referrer_url.endswith(admin_create_organisation_url) and self.request.GET.get("organisation_created"):
                context["show_messages"] = [_("Organisation Created")]

        return context
