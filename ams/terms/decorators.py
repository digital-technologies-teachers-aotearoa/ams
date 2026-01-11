"""Decorators for terms enforcement."""

from functools import wraps
from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from django.urls import reverse

from ams.terms.helpers import get_pending_term_versions_for_user


def terms_required(view_func):
    """
    Decorator to enforce terms acceptance before accessing a function-based view.

    Redirects to terms acceptance flow if user has pending terms.
    Preserves original URL via 'next' parameter for post-acceptance redirect.

    Usage:
        @terms_required
        @login_required
        def my_view(request):
            pass

    Note: Should be placed BEFORE @login_required to ensure
          authentication is checked first.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Only check for authenticated users
        if request.user.is_authenticated:
            pending_versions = get_pending_term_versions_for_user(request.user)

            if pending_versions:
                # Build redirect URL with 'next' parameter
                next_url = request.get_full_path()
                accept_url = reverse("terms:accept")
                redirect_url = f"{accept_url}?{urlencode({'next': next_url})}"
                return HttpResponseRedirect(redirect_url)

        return view_func(request, *args, **kwargs)

    return wrapper
