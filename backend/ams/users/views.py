from functools import partial
from hashlib import sha256
from typing import Any, Dict, List, Optional
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.db import transaction
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
from django_filters.views import FilterView
from django_tables2 import MultiTableMixin, SingleTableMixin, SingleTableView, Table
from registration.models import RegistrationProfile

from ams.billing.invoice import (
    BillingDetailUpdateException,
    BillingException,
    create_membership_option_invoice,
)
from ams.billing.models import Account
from ams.billing.tables import InvoiceTable

from ..base.models import EmailConfirmationPage
from ..forum.views import forum_sync_user_profile
from .filters import UserMembershipFilter
from .forms import (
    AddOrganisationMembershipForm,
    AddUserMembershipForm,
    EditUserProfileForm,
    IndividualRegistrationForm,
    InviteOrganisationMemberForm,
    MembershipOptionForm,
    OrganisationForm,
    OrganisationUserRegistrationForm,
    UploadProfileImageForm,
)
from .models import (
    MembershipOption,
    MembershipStatus,
    Organisation,
    OrganisationMember,
    OrganisationMembership,
    UserMembership,
    UserProfile,
)
from .tables import (
    AdminMembershipOptionTable,
    AdminOrganisationTable,
    AdminUserDetailMembershipTable,
    AdminUserDetailOrganisationMemberTable,
    AdminUserMembershipTable,
    AdminUserTable,
    OrganisationMembershipTable,
    OrganisationMemberTable,
    UserDetailMembershipTable,
    UserDetailOrganisationMemberTable,
)
from .utils import UserIsAdminMixin, user_is_admin, user_message


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

            Account.objects.create(user=new_user)

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
            organisation: Organisation = form.save()

            Account.objects.create(organisation=organisation)

            admin_organisations_url = reverse("admin-organisations")
            return HttpResponseRedirect(admin_organisations_url + "?organisation_created=true")
    else:
        form = OrganisationForm()

    return render(
        request,
        "edit_organisation.html",
        {
            "form": form,
        },
    )


def user_is_organisation_admin(user: User, organisation_id: int) -> bool:
    if not user.is_active:
        return False

    if user.is_staff:
        return True

    is_organisation_admin: bool = OrganisationMember.objects.filter(
        user=user, user__is_active=True, accepted_datetime__isnull=False, organisation_id=organisation_id, is_admin=True
    ).exists()

    return is_organisation_admin


@login_required
def edit_organisation(request: HttpRequest, pk: int) -> HttpResponse:
    if not user_is_admin(request) and not user_is_organisation_admin(request.user, pk):
        return HttpResponse(status=403)

    organisation = Organisation.objects.get(pk=pk)

    if request.method == "POST":
        form = OrganisationForm(request.POST, instance=organisation)
        if form.is_valid():
            form.save()

            admin_organisations_url = reverse("admin-organisations")
            return HttpResponseRedirect(admin_organisations_url + "?organisation_updated=true")
    else:
        form = OrganisationForm(instance=organisation)

    return render(
        request,
        "edit_organisation.html",
        {
            "organisation": organisation,
            "form": form,
        },
    )


class UserIsOrganisationAdminMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        # Only valid for organisation urls with pk in url
        if not self.request.path.startswith("/users/organisations/") or not self.kwargs.get("pk"):
            return False

        organisation_id = self.kwargs.get("pk")
        return user_is_organisation_admin(self.request.user, organisation_id)


class OrganisationDetailView(UserIsOrganisationAdminMixin, MultiTableMixin, DetailView):
    model = Organisation
    template_name = "organisation_view.html"

    def get_tables(self) -> List[Table]:
        return [
            OrganisationMemberTable(self.object.organisation_members.select_related("user").all()),
            OrganisationMembershipTable(self.object.organisation_memberships.select_related("membership_option").all()),
            InvoiceTable(self.object.account.invoices.all()),
        ]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        referrer_url = self.request.META.get("HTTP_REFERER")

        if referrer_url:
            if referrer_url.find("/organisations/invite/") != -1 and self.request.GET.get("invite_sent"):
                context["show_messages"] = [user_message(_("Invite Sent"))]

            elif referrer_url.find("/organisations/view/") != -1:
                if self.request.GET.get("member_removed"):
                    context["show_messages"] = [user_message(_("Organisation Member Removed"))]
                elif self.request.GET.get("made_admin"):
                    context["show_messages"] = [user_message(_("Admin Role Added"))]
                elif self.request.GET.get("revoked_admin"):
                    context["show_messages"] = [user_message(_("Admin Role Revoked"))]

            elif referrer_url.find("/organisations/add-membership/") != -1:
                if self.request.GET.get("membership_added"):
                    context["show_messages"] = [user_message(_("Membership Added"))]

        return context

    def post(self, request: HttpRequest, pk: int, *args: Any, **kwargs: Any) -> HttpResponse:
        organisation = Organisation.objects.get(pk=pk)

        if request.POST.get("action") == "remove_organisation_member":
            try:
                organisation_member_id = int(request.POST["organisation_member_id"])

                organisation_member = OrganisationMember.objects.get(
                    pk=organisation_member_id, organisation=organisation
                )
                organisation_member.delete()

                redirect_url = reverse("view-organisation", kwargs={"pk": pk}) + "?member_removed=true"
                return HttpResponseRedirect(redirect_url)
            except Exception:
                return HttpResponse(status=400)

        elif request.POST.get("action") == "make_organisation_admin":
            try:
                organisation_member_id = int(request.POST["organisation_member_id"])
                organisation_member = OrganisationMember.objects.get(
                    pk=organisation_member_id, organisation=organisation
                )

                if organisation_member.is_active():
                    organisation_member.is_admin = True
                    organisation_member.save()

                    redirect_url = reverse("view-organisation", kwargs={"pk": pk}) + "?made_admin=true"
                    return HttpResponseRedirect(redirect_url)
            except Exception:
                return HttpResponse(status=400)

        elif request.POST.get("action") == "revoke_organisation_admin":
            try:
                organisation_member_id = int(request.POST["organisation_member_id"])
                organisation_member = OrganisationMember.objects.get(
                    pk=organisation_member_id, organisation=organisation
                )
                organisation_member.is_admin = False
                organisation_member.save()

                redirect_url = reverse("view-organisation", kwargs={"pk": pk}) + "?revoked_admin=true"
                return HttpResponseRedirect(redirect_url)
            except Exception:
                return HttpResponse(status=400)

        return HttpResponse(status=400)


def invite_user_to_organisation(
    request: HttpRequest, user: User, organisation: Organisation, invite_token: str
) -> None:
    site = get_current_site(request)
    from_email = settings.DEFAULT_FROM_EMAIL

    subject = _("You are invited to join %(organisation_name)s") % {"organisation_name": organisation.name}
    template = "invite_user_to_organisation.txt"
    context = {
        "site": site,
        "user": user,
        "organisation": organisation,
        "invite_token": invite_token,
    }

    message = render_to_string(template, context, request=request)

    send_mail(subject, message, from_email, [user.email])


def invite_email_to_organisation(
    request: HttpRequest, email: str, organisation: Organisation, invite_token: str
) -> None:
    site = get_current_site(request)
    from_email = settings.DEFAULT_FROM_EMAIL

    subject = _("You are invited to join %(organisation_name)s") % {"organisation_name": organisation.name}
    template = "invite_email_to_organisation.txt"
    context = {
        "site": site,
        "email": email,
        "organisation": organisation,
        "invite_token": invite_token,
    }

    message = render_to_string(template, context, request=request)

    send_mail(subject, message, from_email, [email])


@login_required
def invite_organisation_member(request: HttpRequest, pk: int) -> HttpResponse:
    if not user_is_admin(request) and not user_is_organisation_admin(request.user, pk):
        return HttpResponse(status=403)

    organisation = Organisation.objects.get(pk=pk)

    if request.method == "POST":
        form = InviteOrganisationMemberForm(organisation, request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            email = form_data["email"]

            user: Optional[User] = User.objects.filter(email=email).first()

            invite_token = sha256(str(uuid4()).encode()).hexdigest()

            if user:
                transaction.on_commit(
                    partial(
                        invite_user_to_organisation,
                        request=request,
                        user=user,
                        organisation=organisation,
                        invite_token=invite_token,
                    )
                )
            else:
                transaction.on_commit(
                    partial(
                        invite_email_to_organisation,
                        request=request,
                        email=email,
                        organisation=organisation,
                        invite_token=invite_token,
                    )
                )

            OrganisationMember.objects.create(
                user=user,
                invite_email=email,
                invite_token=invite_token,
                organisation=organisation,
                created_datetime=timezone.localtime(),
            )

            view_organisation_url = reverse("view-organisation", kwargs={"pk": organisation.pk})
            return HttpResponseRedirect(view_organisation_url + "?invite_sent=true")

    else:
        form = InviteOrganisationMemberForm(organisation)

    return render(
        request,
        "invite_organisation_member.html",
        {
            "organisation": organisation,
            "form": form,
        },
    )


@login_required
def accept_organisation_user_invite(request: HttpRequest, invite_token: str) -> HttpResponse:
    organisation_member = OrganisationMember.objects.filter(
        invite_token=invite_token,
        user__isnull=False,
    ).first()

    if not organisation_member:
        return HttpResponse(status=400)

    if organisation_member.user != request.user:
        # If logged in as a different user send them back to the login screen
        next = reverse("accept-organisation-user-invite", kwargs={"invite_token": invite_token})
        return redirect_to_login(next)

    if not organisation_member.accepted_datetime:
        organisation_member.accepted_datetime = timezone.localtime()
        organisation_member.save()

    organisation = organisation_member.organisation

    return render(
        request,
        "organisation_invite_accepted.html",
        {
            "organisation": organisation,
        },
    )


def register_organisation_member(request: HttpRequest, invite_token: str) -> HttpResponse:
    organisation_member = OrganisationMember.objects.filter(
        invite_token=invite_token, user__isnull=True, accepted_datetime__isnull=True
    ).first()

    if not organisation_member:
        return HttpResponse(status=400)

    if request.method == "POST":
        form = OrganisationUserRegistrationForm(request.POST, initial={"email": organisation_member.invite_email})

        if form.is_valid():
            form_data = form.cleaned_data

            new_user = RegistrationProfile.objects.create_inactive_user(
                get_current_site(request),
                send_email=True,
                username=organisation_member.invite_email,
                email=organisation_member.invite_email,
                first_name=form_data["first_name"],
                last_name=form_data["last_name"],
                password=form_data["password"],
            )

            Account.objects.create(user=new_user)

            organisation_member.user = new_user
            organisation_member.accepted_datetime = timezone.localtime()
            organisation_member.save()

            return render(
                request,
                "individual_registration_pending.html",
                status=201,
            )
    else:
        form = OrganisationUserRegistrationForm(initial={"email": organisation_member.invite_email})

    organisation = organisation_member.organisation

    return render(
        request,
        "organisation_user_registration.html",
        {
            "form": form,
            "organisation": organisation,
        },
    )


def notify_staff_of_new_user_with_membership(request: HttpRequest, new_user: User) -> HttpResponse:
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
            if user.user_memberships.exists():
                transaction.on_commit(partial(notify_staff_of_new_user_with_membership, request=request, new_user=user))

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

            forum_sync_user_profile(user)

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


def notify_staff_of_new_user_membership(request: HttpRequest, user_membership: UserMembership) -> None:
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


def notify_staff_of_new_organisation_membership(
    request: HttpRequest, organisation_membership: OrganisationMembership
) -> None:
    site = get_current_site(request)
    from_email = settings.DEFAULT_FROM_EMAIL

    staff_users = User.objects.filter(is_staff=True, is_active=True)
    for user in staff_users:
        subject = _("New organisation membership")
        template = "new_organisation_membership_email.txt"
        context = {
            "user": user,
            "organisation": organisation_membership.organisation,
            "site": site,
        }

        message = render_to_string(template, context, request=request)

        send_mail(subject, message, from_email, [user.email])


add_membership_billing_details_error_message = user_message(
    _(
        "The billing contact could not be created. "
        "The membership could not be added. "
        "Please try to add the membership again. "
        "If this message reappears please contact the site administrator."
    ),
    message_type="error",
)


add_membership_invoice_error_message = user_message(
    _(
        "The invoice could not be created. "
        "The membership could not be added. "
        "Please try to add the membership again. "
        "If this message reappears please contact the site administrator."
    ),
    message_type="error",
)


@login_required
def add_user_membership(request: HttpRequest, pk: int) -> HttpResponse:
    if not (user_is_admin(request) or request.user.pk == pk):
        return HttpResponse(status=401)

    user = User.objects.get(pk=pk)
    current_membership = user.get_current_user_membership()

    if user_is_admin(request):
        user_view_url = reverse("admin-user-view", kwargs={"pk": pk})
    else:
        user_view_url = reverse("current-user-view")

    billing_exception: Optional[BillingException] = None

    if request.method == "POST":
        form = AddUserMembershipForm(request.POST, user=user)

        if form.is_valid():
            form_data = form.cleaned_data
            membership_option = MembershipOption.objects.get(name=form_data["membership_option"])

            try:
                invoice = create_membership_option_invoice(user.account, membership_option)

                user_membership = UserMembership.objects.create(
                    user=user,
                    membership_option=membership_option,
                    start_date=form_data["start_date"],
                    created_datetime=timezone.localtime(),
                    invoice=invoice,
                )

                transaction.on_commit(
                    partial(notify_staff_of_new_user_membership, request=request, user_membership=user_membership)
                )

                return HttpResponseRedirect(user_view_url + "?membership_added=true")

            except BillingException as e:
                billing_exception = e
    else:
        start_date = timezone.localdate()

        if current_membership:
            membership_expiry_date = current_membership.expiry_date()

            if membership_expiry_date > timezone.localdate():
                start_date = membership_expiry_date

        initial_values = {"start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT)}

        form = AddUserMembershipForm(initial=initial_values, user=user)

    messages: List[Dict[str, Any]] = []
    if billing_exception:
        if isinstance(billing_exception, BillingDetailUpdateException):
            messages.append(add_membership_billing_details_error_message)
        else:
            messages.append(add_membership_invoice_error_message)

    return render(
        request,
        "add_user_membership.html",
        {
            "user_view_url": user_view_url,
            "current_membership": current_membership,
            "user_detail": user,
            "form": form,
            "show_messages": messages,
        },
    )


@login_required
def add_organisation_membership(request: HttpRequest, pk: int) -> HttpResponse:
    if not (user_is_admin(request) or user_is_organisation_admin(request.user, pk)):
        return HttpResponse(status=401)

    organisation = Organisation.objects.get(pk=pk)

    current_membership = (
        organisation.organisation_memberships.filter(
            cancelled_datetime__isnull=True, start_date__lte=timezone.localdate()
        )
        .order_by("-start_date")
        .first()
    )

    latest_membership = organisation.organisation_memberships.order_by("-start_date").first()

    billing_exception: Optional[BillingException] = None

    if request.method == "POST":
        form = AddOrganisationMembershipForm(request.POST, organisation=organisation)
        if form.is_valid():
            form_data = form.cleaned_data
            membership_option = MembershipOption.objects.get(name=form_data["membership_option"])

            try:
                invoice = create_membership_option_invoice(organisation.account, membership_option)

                organisation_membership = OrganisationMembership.objects.create(
                    organisation=organisation,
                    membership_option=membership_option,
                    start_date=form_data["start_date"],
                    created_datetime=timezone.localtime(),
                    invoice=invoice,
                )

                transaction.on_commit(
                    partial(
                        notify_staff_of_new_organisation_membership,
                        request=request,
                        organisation_membership=organisation_membership,
                    )
                )

                view_organisation_url = reverse("view-organisation", kwargs={"pk": pk})
                return HttpResponseRedirect(view_organisation_url + "?membership_added=true")

            except BillingException as e:
                billing_exception = e

    else:
        start_date = timezone.localdate()

        if current_membership and current_membership.status() == MembershipStatus.ACTIVE:
            membership_expiry_date = current_membership.expiry_date()

            if membership_expiry_date > timezone.localdate():
                start_date = membership_expiry_date

        initial_values = {"start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT)}

        form = AddOrganisationMembershipForm(initial=initial_values, organisation=organisation)

    messages: List[Dict[str, Any]] = []

    if billing_exception:
        if isinstance(billing_exception, BillingDetailUpdateException):
            messages.append(add_membership_billing_details_error_message)
        else:
            messages.append(add_membership_invoice_error_message)

    return render(
        request,
        "add_organisation_membership.html",
        {
            "form": form,
            "organisation": organisation,
            "current_membership": current_membership,
            "latest_membership": latest_membership,
            "show_messages": messages,
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
            context["show_messages"] = [user_message(_("Membership Cancelled"))]

        if request.method == "GET" and request.GET.get("membership_approved"):
            context["show_messages"] = [user_message(_("Membership Approved"))]

        return context


class AdminUserMembershipListView(UserIsAdminMixin, SingleTableMixin, FilterView, MembershipActionMixin):
    model = UserMembership
    table_class = AdminUserMembershipTable
    template_name = "admin_user_memberships.html"
    filterset_class = UserMembershipFilter

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
            context["show_messages"] = [user_message(_("Membership Option Added"))]

        if self.request.method == "GET" and self.request.GET.get("membership_option_updated"):
            context["show_messages"] = [user_message(_("Membership Option Saved"))]

        return context


class UserDetailViewBase(MultiTableMixin, DetailView):
    model = User
    template_name = "user_view.html"
    context_object_name = "user_detail"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        user = context["user_detail"]

        latest_membership = user.get_latest_user_membership()
        can_add_membership = False
        if not latest_membership or latest_membership.status() in [MembershipStatus.ACTIVE, MembershipStatus.EXPIRED]:
            can_add_membership = True

        context["can_add_membership"] = can_add_membership

        if self.request.method == "GET":
            if self.request.GET.get("profile_updated"):
                context["show_messages"] = [user_message(_("Profile Updated"))]

            if self.request.GET.get("requires_membership"):
                context["show_messages"] = [
                    user_message(_("You must have an active membership to view this feature."), "error")
                ]

            if self.request.GET.get("invalid_profile_image"):
                context["show_messages"] = [
                    user_message(
                        _("Your profile image must be valid JPG, PNG or GIF not exceeding 1MB in size."), "error"
                    )
                ]

        return context

    def user_post_action(self, request: HttpRequest, user_view_url: str, user: User) -> Optional[HttpResponse]:
        if request.POST.get("action") == "upload_profile_image":
            form = UploadProfileImageForm(request.POST, request.FILES)
            if form.is_valid():
                form_data = form.cleaned_data

                try:
                    user_profile = user.profile
                except UserProfile.DoesNotExist:
                    user_profile = UserProfile(user=user)
                    user_profile.save()

                # If user has an existing profile image, delete it
                if user_profile.image != "" and default_storage.exists(user_profile.image):
                    default_storage.delete(user_profile.image)

                profile_image_file = form_data["profile_image_file"]

                image_file_extensions = {
                    "image/jpeg": "jpg",
                    "image/png": "png",
                    "image/gif": "gif",
                }

                # Save to MEDIA_ROOT directory
                timestamp = int(timezone.now().timestamp())
                extension = image_file_extensions[profile_image_file.content_type]
                image_file_path = f"user/profiles/user_{user.pk}_{timestamp}.{extension}"

                default_storage.save(image_file_path, profile_image_file)

                user_profile.image = image_file_path
                user_profile.save()

                forum_sync_user_profile(user)

                return HttpResponseRedirect(user_view_url)
            else:
                return HttpResponseRedirect(user_view_url + "?invalid_profile_image=true")

        return None


class UserDetailView(LoginRequiredMixin, UserDetailViewBase):
    def get_tables(self) -> List[Table]:
        return [
            UserDetailMembershipTable(self.object.user_memberships.all()),
            InvoiceTable(self.object.account.invoices.all()),
            UserDetailOrganisationMemberTable(self.object.organisation_members.select_related("user").all()),
        ]

    def get_object(self) -> User:
        return User.objects.get(id=self.request.user.pk)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if user_is_admin(request):
            # Redirect to admin user view
            return HttpResponseRedirect(f"/users/view/{request.user.pk}/")
        return super().get(request, args, kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()

        response = self.user_post_action(request, reverse("current-user-view"), self.request.user)
        if response:
            return response

        return HttpResponse(status=400)


class AdminUserDetailView(UserIsAdminMixin, UserDetailViewBase, MembershipActionMixin):
    def get_tables(self) -> List[Table]:
        return [
            AdminUserDetailMembershipTable(self.object.user_memberships.all()),
            InvoiceTable(self.object.account.invoices.all()),
            AdminUserDetailOrganisationMemberTable(self.object.organisation_members.select_related("user").all()),
        ]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        redirect_url = reverse("admin-user-view", kwargs={"pk": self.object.pk})

        response = self.user_post_action(request, redirect_url, self.object)
        if response:
            return response

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
                context["show_messages"] = [user_message(_("Organisation Created"))]

            if referrer_url.find("/organisations/edit/") != -1 and self.request.GET.get("organisation_updated"):
                context["show_messages"] = [user_message(_("Organisation Saved"))]

        return context
