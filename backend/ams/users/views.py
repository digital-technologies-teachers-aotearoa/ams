from typing import Optional

from django.conf import settings
from django.contrib.sites.requests import RequestSite
from django.forms import BoundField
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from registration.models import RegistrationProfile

from ..base.models import EmailConfirmationPage
from .forms import IndividualRegistrationForm
from .models import MembershipOption, UserMembership


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
