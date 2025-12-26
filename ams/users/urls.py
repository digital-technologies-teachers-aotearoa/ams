from django.urls import path

from .views import organisation_create_view
from .views import organisation_detail_view
from .views import organisation_update_view
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    # Organisation management
    path(
        "organisations/create/",
        view=organisation_create_view,
        name="organisation_create",
    ),
    path(
        "organisations/view/<uuid:uuid>/",
        view=organisation_detail_view,
        name="organisation_detail",
    ),
    path(
        "organisations/edit/<uuid:uuid>/",
        view=organisation_update_view,
        name="organisation_update",
    ),
]
