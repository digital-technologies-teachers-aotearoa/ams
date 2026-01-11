"""Views for terms acceptance."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from ams.terms.forms import TermAcceptanceForm
from ams.terms.helpers import get_latest_term_versions
from ams.terms.helpers import get_pending_term_versions_for_user
from ams.terms.helpers import invalidate_pending_terms_cache
from ams.terms.models import TermAcceptance


def get_client_ip(request):
    """
    Extract client IP address from request.

    Handles X-Forwarded-For header for proxied requests.

    Args:
        request: Django HttpRequest object

    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@login_required
@require_http_methods(["GET", "POST"])
def accept_terms_view(request):
    """
    Display and handle acceptance of pending terms.

    Shows one TermVersion at a time in deterministic order.
    On POST, records acceptance and redirects to next term or original destination.

    GET: Display the first pending term with acceptance form
    POST: Record acceptance, invalidate cache, redirect to next term or destination
    """
    pending_versions = get_pending_term_versions_for_user(request.user)

    # If no pending terms, redirect to 'next' or home
    if not pending_versions:
        next_url = request.GET.get("next") or request.POST.get("next")
        if next_url:
            return HttpResponseRedirect(next_url)
        return HttpResponseRedirect(reverse("root_redirect"))

    # Show first pending version (deterministic order from helper)
    term_version = pending_versions[0]

    if request.method == "POST":
        form = TermAcceptanceForm(request.POST, term_version=term_version)
        if form.is_valid():
            # Record acceptance
            TermAcceptance.objects.create(
                user=request.user,
                term_version=term_version,
                ip_address=get_client_ip(request),
                # Truncate for safety
                user_agent=request.headers.get("user-agent", "")[:500],
                source="web",
            )

            # Invalidate cache
            invalidate_pending_terms_cache(request.user)

            # Redirect to self with same 'next' parameter
            # This will show the next pending term, or redirect to destination
            next_url = form.cleaned_data.get("next", "")
            redirect_url = reverse("terms:accept")
            if next_url:
                redirect_url += f"?next={next_url}"
            return HttpResponseRedirect(redirect_url)
    else:
        # GET: Create form with initial 'next' value
        form = TermAcceptanceForm(
            initial={"next": request.GET.get("next", "")},
            term_version=term_version,
        )

    # Display term
    context = {
        "form": form,
        "term_version": term_version,
        "pending_count": len(pending_versions),
        "current_position": 1,  # Always showing first of pending list
    }

    return render(request, "terms/accept.html", context)


def terms_list_view(request):
    """
    Display all latest term versions.

    Shows the current active version of each term. Accessible to all users
    (authenticated and anonymous) for transparency.

    Returns:
        Rendered terms list template
    """
    term_versions = get_latest_term_versions()

    context = {
        "term_versions": term_versions,
    }

    return render(request, "terms/list.html", context)
