from os import environ

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.urls import reverse
from pydiscourse.sso import sso_redirect_url, sso_validate

from ..users.models import UserMemberStatus
from ..users.utils import user_is_admin


@login_required
def forum_sso_login_redirect(request: HttpRequest) -> HttpResponse:
    return HttpResponseRedirect(environ["DISCOURSE_REDIRECT_DOMAIN"] + "/session/sso?return_path=/")


@login_required
def forum_sso_login_callback(request: HttpRequest) -> HttpResponse:
    if user_is_admin(request) or request.user.member.status() == UserMemberStatus.ACTIVE:
        # Active member - they can see the forum
        secret = environ["DISCOURSE_CONNECT_SECRET"]

        payload = request.GET.get("sso")
        signature = request.GET.get("sig")

        nonce = sso_validate(payload, signature, secret)
        redirect_url = sso_redirect_url(nonce, secret, request.user.email, request.user.id, request.user.username)
        return HttpResponseRedirect(environ["DISCOURSE_REDIRECT_DOMAIN"] + redirect_url)

    else:
        # Not active member - give them a redirect
        redirect_url = reverse("current-user-view") + "?requires_membership=true"

        return HttpResponseRedirect(redirect_url)
