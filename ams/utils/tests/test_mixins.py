from unittest.mock import MagicMock

from django.http import HttpResponsePermanentRedirect
from django.test import RequestFactory

from ams.utils.mixins import RedirectToCosmeticURLMixin


class ConcreteView(RedirectToCosmeticURLMixin):
    """Minimal concrete view for testing the mixin."""

    def get_object(self):
        return self.object_to_return

    def get_context_data(self, **kwargs):
        return {"object": kwargs.get("object")}

    def render_to_response(self, context):
        return MagicMock(name="rendered_response", context=context)


class TestRedirectToCosmeticURLMixin:
    def setup_method(self):
        self.factory = RequestFactory()
        self.view = ConcreteView()
        self.obj = MagicMock()

    def test_redirects_when_path_differs_from_canonical_url(self):
        self.obj.get_absolute_url.return_value = "/events/1/my-event/"
        self.view.object_to_return = self.obj
        request = self.factory.get("/events/1/")

        response = self.view.get(request)

        assert isinstance(response, HttpResponsePermanentRedirect)
        assert response["Location"] == "/events/1/my-event/"

    def test_renders_normally_when_path_matches_canonical_url(self):
        self.obj.get_absolute_url.return_value = "/events/1/my-event/"
        self.view.object_to_return = self.obj
        request = self.factory.get("/events/1/my-event/")

        response = self.view.get(request)

        assert not isinstance(response, HttpResponsePermanentRedirect)
        assert response.context == {"object": self.obj}

    def test_sets_object_from_get_object(self):
        self.obj.get_absolute_url.return_value = "/events/1/my-event/"
        self.view.object_to_return = self.obj
        request = self.factory.get("/events/1/my-event/")

        self.view.get(request)

        assert self.view.object is self.obj
