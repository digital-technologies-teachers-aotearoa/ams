from django.urls import path

from . import views

app_name = "organisations"

urlpatterns = [
    path("create/", views.organisation_create_view, name="create"),
    path("<uuid:uuid>/", views.organisation_detail_view, name="detail"),
    path("<uuid:uuid>/update/", views.organisation_update_view, name="update"),
    path(
        "<uuid:uuid>/invite/",
        views.organisation_invite_member_view,
        name="invite_member",
    ),
    path(
        "invite/<uuid:invite_token>/accept/",
        views.accept_organisation_invite_view,
        name="accept_invite",
    ),
    path(
        "invite/<uuid:invite_token>/decline/",
        views.decline_organisation_invite_view,
        name="decline_invite",
    ),
]
