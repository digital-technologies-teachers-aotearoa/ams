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
    path(
        "<uuid:uuid>/member/<uuid:member_uuid>/remove/",
        views.remove_organisation_member_view,
        name="remove_member",
    ),
    path(
        "<uuid:uuid>/member/<uuid:member_uuid>/make-admin/",
        views.make_organisation_admin_view,
        name="make_admin",
    ),
    path(
        "<uuid:uuid>/member/<uuid:member_uuid>/revoke-admin/",
        views.revoke_organisation_admin_view,
        name="revoke_admin",
    ),
    path(
        "<uuid:uuid>/leave/",
        views.leave_organisation_view,
        name="leave",
    ),
    path(
        "<uuid:uuid>/deactivate/",
        views.deactivate_organisation_view,
        name="deactivate",
    ),
    path(
        "<uuid:uuid>/member/<uuid:member_uuid>/revoke-invite/",
        views.revoke_organisation_invite_view,
        name="revoke_invite",
    ),
    path(
        "<uuid:uuid>/member/<uuid:member_uuid>/resend-invite/",
        views.resend_organisation_invite_view,
        name="resend_invite",
    ),
]
