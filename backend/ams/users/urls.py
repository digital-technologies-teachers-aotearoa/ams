from django.urls import include, path

from .views import (
    AdminOrganisationListView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserMembershipListView,
    UserDetailView,
    activate_user,
    add_user_membership,
    create_organisation,
    edit_user_profile,
    individual_registration,
)

urlpatterns = [
    path("list/", AdminUserListView.as_view(), name="admin-user-list"),
    path("current/", UserDetailView.as_view(), name="current-user-view"),
    path("edit/<int:pk>/", edit_user_profile, name="edit-user-profile"),
    path("view/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-view"),
    path("add-membership/<int:pk>/", add_user_membership, name="add-user-membership"),
    path("memberships/", AdminUserMembershipListView.as_view(), name="admin-user-memberships"),
    path("organisations/", AdminOrganisationListView.as_view(), name="admin-organisations"),
    path("organisations/create/", create_organisation, name="admin-create-organisation"),
    path("individual-registration/", individual_registration, name="registration_register"),
    path("activate/<str:activation_key>/", activate_user, name="activate-user"),
    path("", include("registration.auth_urls")),
]
