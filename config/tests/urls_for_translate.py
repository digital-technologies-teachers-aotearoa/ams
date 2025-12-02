from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponse
from django.urls import path


def dummy_view(request):
    return HttpResponse("ok")


urlpatterns = i18n_patterns(
    path("another/page/", dummy_view, name="another"),
    path("plain/path/", dummy_view, name="plain"),
    path("current/page/", dummy_view, name="current"),
    path("", dummy_view, name="root"),
)
