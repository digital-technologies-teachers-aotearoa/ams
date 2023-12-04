from os import environ
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.urls import reverse
from pydiscourse import DiscourseClient
from pydiscourse.sso import sso_redirect_url, sso_validate

from ..users.models import MembershipStatus, UserProfile
from ..users.utils import user_is_admin


def forum_sync_user_profile(user: User) -> Optional[Dict[str, Any]]:
    discourse_api_key = settings.DISCOURSE_API_KEY
    if not discourse_api_key:
        return None

    client = DiscourseClient(
        "http://discourse", api_username=settings.DISCOURSE_API_USERNAME, api_key=discourse_api_key
    )

    user.refresh_from_db()

    # TODO: maybe replace with an editable forum username or change how we approach usernames
    # as discourse displays the username on posts. Our usernames are currently email addresses
    username = user.username
    name = user.display_name
    avatar_url = None

    try:
        user_image_path = user.profile.image
        if user_image_path:
            if settings.DEBUG:
                proto = "http"
            else:
                proto = "https"

            web_host = environ["APPLICATION_WEB_HOST"]
            avatar_url = f"{proto}://{web_host}{settings.MEDIA_URL}{user_image_path}"

    except UserProfile.DoesNotExist:
        pass

    response: Dict[str, Any] = client.sync_sso(
        sso_secret=settings.DISCOURSE_CONNECT_SECRET,
        name=name,
        username=username,
        email=user.email,
        external_id=user.id,
        avatar_url=avatar_url,
    )
    return response


@login_required
def forum_sso_login_redirect(request: HttpRequest) -> HttpResponse:
    return HttpResponseRedirect(settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso?return_path=/")


@login_required
def forum_sso_login_callback(request: HttpRequest) -> HttpResponse:
    if user_is_admin(request) or request.user.member.status() == MembershipStatus.ACTIVE:
        # Active member - they can see the forum
        secret = settings.DISCOURSE_CONNECT_SECRET

        payload = request.GET.get("sso")
        signature = request.GET.get("sig")

        nonce = sso_validate(payload, signature, secret)

        # TODO: maybe replace with an editable forum username or change how we approach usernames
        # as discourse displays the username on posts. Our usernames are currently email addresses
        username = request.user.username
        name = request.user.display_name
        external_id = request.user.id

        redirect_url = sso_redirect_url(nonce, secret, request.user.email, external_id, username, name=name)

        return HttpResponseRedirect(settings.DISCOURSE_REDIRECT_DOMAIN + redirect_url)

    else:
        # Not active member - give them a redirect
        redirect_url = reverse("current-user-view") + "?requires_membership=true"

        return HttpResponseRedirect(redirect_url)
