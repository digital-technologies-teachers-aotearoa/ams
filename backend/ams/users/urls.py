from django.urls import include, path

from .views import (
    AdminOrganisationListView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserMembershipListView,
    activate_user,
    create_organisation,
    individual_registration,
)

urlpatterns = [
    path("list/", AdminUserListView.as_view(), name="admin-user-list"),
    path("view/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-view"),
    path("memberships/", AdminUserMembershipListView.as_view(), name="admin-user-memberships"),
    path("organisations/", AdminOrganisationListView.as_view(), name="admin-organisations"),
    path("organisations/create/", create_organisation, name="admin-create-organisation"),
    path("individual-registration/", individual_registration, name="registration_register"),
    path("activate/<str:activation_key>/", activate_user, name="activate-user"),
    path("", include("registration.auth_urls")),
]
