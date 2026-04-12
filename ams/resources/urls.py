from django.urls import path

from ams.resources import views

app_name = "resources"
urlpatterns = [
    path(
        "",
        views.ResourceHomeView.as_view(),
        name="home",
    ),
    path(
        "resource/<int:pk>/",
        views.ResourceDetailView.as_view(),
    ),
    path(
        "resource/<int:pk>/<slug:slug>/",
        views.ResourceDetailView.as_view(),
        name="resource",
    ),
    path(
        "component/<int:pk>/download/",
        views.ResourceComponentDownloadView.as_view(),
        name="component_download",
    ),
]
