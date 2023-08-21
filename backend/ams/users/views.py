from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.requests import RequestSite
from django.db.models import QuerySet
from django.forms import BoundField
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django_tables2 import SingleTableMixin, SingleTableView
from registration.models import RegistrationProfile

from ..base.models import EmailConfirmationPage
from .forms import IndividualRegistrationForm, OrganisationForm
from .models import MembershipOption, Organisation, UserMembership
from .tables import (
    AdminOrganisationTable,
    AdminUserDetailMembershipTable,
    AdminUserMembershipTable,
    AdminUserTable,
)
from .utils import UserIsAdminMixin, user_is_admin


def individual_registration(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = IndividualRegistrationForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            # Create a new user using their email as the username and send activation email
            new_user = RegistrationProfile.objects.create_inactive_user(
                RequestSite(request),
                send_email=True,
                username=form_data["email"],
                email=form_data["email"],
                first_name=form_data["first_name"],
                last_name=form_data["last_name"],
                password=form_data["password"],
            )

            membership_option = MembershipOption.objects.get(name=form_data["membership_option"])
            UserMembership.objects.create(
                user=new_user, membership_option=membership_option, created_datetime=timezone.now()
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


def activate_user(request: HttpRequest, activation_key: str) -> HttpResponse:
    user, activation_successful = RegistrationProfile.objects.activate_user(activation_key, RequestSite(request))

    if user:
        if activation_successful:
            email_confirmation_page = EmailConfirmationPage.objects.get(
                live=True, locale__language_code=settings.LANGUAGE_CODE
            )
            return email_confirmation_page.serve(request)
        elif user.is_active:
            return HttpResponseRedirect("/")

    return HttpResponse(status=401)


class AdminUserListView(UserIsAdminMixin, SingleTableView):
    model = User
    table_class = AdminUserTable
    template_name = "admin_user_list.html"


def approve_user_membership(user_membership_id: int) -> HttpResponse:
    user_membership = UserMembership.objects.get(pk=user_membership_id)

    if not user_membership.approved_datetime:
        user_membership.approved_datetime = timezone.now()
        user_membership.save()
        return True

    return False


class AdminUserMembershipListView(UserIsAdminMixin, SingleTableView):
    model = UserMembership
    table_class = AdminUserMembershipTable
    template_name = "admin_user_memberships.html"

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.POST.get("action") == "approve_user_membership":
            try:
                user_membership_id = int(request.POST["user_membership_id"])
                membership_approved = approve_user_membership(user_membership_id)
            except Exception:
                return HttpResponse(status=400)
        else:
            return HttpResponse(status=400)

        self.object_list = self.get_queryset()
        context = self.get_context_data()

        if membership_approved:
            context["show_messages"] = [_("Membership Approved")]

        return self.render_to_response(context)


class AdminUserDetailView(UserIsAdminMixin, SingleTableMixin, DetailView):
    model = User
    table_class = AdminUserDetailMembershipTable
    template_name = "admin_user_view.html"
    context_object_name = "user_detail"

    def get_table_data(self) -> QuerySet:
        return self.object.user_memberships.all()

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.POST.get("action") == "approve_user_membership":
            try:
                user_membership_id = int(request.POST["user_membership_id"])
                membership_approved = approve_user_membership(user_membership_id)
            except Exception:
                return HttpResponse(status=400)
        else:
            return HttpResponse(status=400)

        self.object = self.get_object()
        context = self.get_context_data()

        if membership_approved:
            context["show_messages"] = [_("Membership Approved")]

        return self.render_to_response(context)


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
