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
        "search/",
        views.ResourceSearchView.as_view(),
        name="search",
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
        "component/<int:pk>/access/",
        views.ResourceComponentAccessView.as_view(),
        name="component_access",
    ),
    path(
        "component/<int:pk>/download/",
        views.ResourceComponentAccessView.as_view(),
        name="component_download",
    ),
]
