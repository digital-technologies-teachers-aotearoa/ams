from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.urls import reverse
from pydiscourse.sso import sso_redirect_url
from pydiscourse.sso import sso_validate

from ams.utils.permissions import user_has_active_membership


@login_required
def forum_sso_login_redirect(request: HttpRequest) -> HttpResponse:
    return HttpResponseRedirect(
        settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso?return_path=/",
    )


@login_required
def forum_sso_login_callback(request: HttpRequest) -> HttpResponse:
    # Check if user has forum access (superuser or active membership)
    if not user_has_active_membership(request.user):
        messages.error(
            request,
            "You must have an active membership to view this feature",
        )
        return HttpResponseRedirect(
            reverse("users:detail", kwargs={"username": request.user.username}),
        )

    secret = settings.DISCOURSE_CONNECT_SECRET

    payload = request.GET.get("sso")
    signature = request.GET.get("sig")

    nonce = sso_validate(payload, signature, secret)

    username = request.user.username
    name = request.user.get_full_name()
    external_id = request.user.id

    redirect_url = sso_redirect_url(
        nonce,
        secret,
        request.user.email,
        external_id,
        username,
        name=name,
    )
    return HttpResponseRedirect(settings.DISCOURSE_REDIRECT_DOMAIN + redirect_url)
