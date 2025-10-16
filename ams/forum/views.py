from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from pydiscourse.sso import sso_redirect_url
from pydiscourse.sso import sso_validate


@login_required
def forum_sso_login_redirect(request: HttpRequest) -> HttpResponse:
    return HttpResponseRedirect(
        settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso?return_path=/",
    )


@login_required
def forum_sso_login_callback(request: HttpRequest) -> HttpResponse:
    # TODO: Check user is admin or a user with an active membership.
    secret = settings.DISCOURSE_CONNECT_SECRET

    payload = request.GET.get("sso")
    signature = request.GET.get("sig")

    nonce = sso_validate(payload, signature, secret)

    # TODO: Replace with an editable forum username or change
    # how we approach usernames as Discourse displays the username
    # on posts. Our usernames are currently the primary key.
    username = request.user.id
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
