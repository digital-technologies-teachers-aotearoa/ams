from django.contrib.auth.models import User
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .forms import IndividualRegistrationForm
from .models import MembershipOption, UserMembership


def individual_registration(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = IndividualRegistrationForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            # Create a new user using their email as the username
            new_user = User.objects.create_user(
                username=form_data["email"], email=form_data["email"], password=form_data["password"]
            )
            new_user.first_name = form_data["first_name"]
            new_user.last_name = form_data["last_name"]
            new_user.is_active = False
            new_user.save()

            membership_option = MembershipOption.objects.get(name=form_data["membership_option"])
            UserMembership.objects.create(
                user=new_user, membership_option=membership_option, created_datetime=timezone.now()
            )

            return render(
                request,
                "individual_registration_pending.html",
                status=201,
            )

    form = IndividualRegistrationForm()

    personal_detail_fields = []
    membership_fields = []

    for field in form:
        if field.name == "membership_option":
            membership_fields.append(field)
        else:
            personal_detail_fields.append(field)

    return render(
        request,
        "individual_registration.html",
        {"personal_detail_fields": personal_detail_fields, "membership_fields": membership_fields},
    )
