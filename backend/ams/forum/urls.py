from django.urls import path

from .views import forum_sso_login_callback, forum_sso_login_redirect

urlpatterns = [
    path("", forum_sso_login_redirect, name="forum-sso-login-redirect"),
    path("sso", forum_sso_login_callback, name="forum-sso-login-callback"),
]
