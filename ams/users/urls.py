from django.urls import path

from ams.users.views import accept_organisation_invite_view
from ams.users.views import decline_organisation_invite_view
from ams.users.views import organisation_create_view
from ams.users.views import organisation_detail_view
from ams.users.views import organisation_invite_member_view
from ams.users.views import organisation_update_view
from ams.users.views import user_detail_view
from ams.users.views import user_redirect_view
from ams.users.views import user_update_view

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
    path(
        "organisations/invite/<uuid:uuid>/",
        view=organisation_invite_member_view,
        name="organisation_invite_member",
    ),
    # Organisation invite acceptance/decline
    path(
        "accept-invite/<uuid:invite_token>/",
        view=accept_organisation_invite_view,
        name="accept_organisation_invite",
    ),
    path(
        "decline-invite/<uuid:invite_token>/",
        view=decline_organisation_invite_view,
        name="decline_organisation_invite",
    ),
]
