from django.urls import include, path

from .views import AdminUserListView, activate_user, individual_registration

urlpatterns = [
    path("list/", AdminUserListView.as_view(), name="admin-user-list"),
    path("individual-registration/", individual_registration, name="registration_register"),
    path("activate/<str:activation_key>/", activate_user, name="activate-user"),
    path("", include("registration.auth_urls")),
]
