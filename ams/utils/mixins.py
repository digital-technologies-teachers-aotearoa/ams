from django.http import HttpResponsePermanentRedirect


class RedirectToCosmeticURLMixin:
    """Redirect to the canonical URL if the request path doesn't match.

    Ensures URLs show the readable slug version (e.g., /event/1/my-event/
    instead of /event/1/). Redirects to get_absolute_url() if the request
    path doesn't match.
    """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        canonical_url = self.object.get_absolute_url()
        if request.path != canonical_url:
            return HttpResponsePermanentRedirect(canonical_url)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
