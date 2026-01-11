"""View mixins for terms enforcement."""

from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from django.urls import reverse

from ams.terms.helpers import get_pending_term_versions_for_user


class TermsRequiredMixin:
    """
    Mixin to enforce terms acceptance before accessing a view.

    Redirects to terms acceptance flow if user has pending terms.
    Preserves original URL via 'next' parameter for post-acceptance redirect.

    Usage:
        class MyView(TermsRequiredMixin, LoginRequiredMixin, View):
            pass

    Note: Should be placed BEFORE LoginRequiredMixin to ensure
          authentication is checked first.
    """

    def dispatch(self, request, *args, **kwargs):
        """Check for pending terms before allowing access."""
        # Only check for authenticated users
        if request.user.is_authenticated:
            pending_versions = get_pending_term_versions_for_user(request.user)

            if pending_versions:
                # Build redirect URL with 'next' parameter
                next_url = request.get_full_path()
                accept_url = reverse("terms:accept")
                redirect_url = f"{accept_url}?{urlencode({'next': next_url})}"
                return HttpResponseRedirect(redirect_url)

        return super().dispatch(request, *args, **kwargs)
