from django.urls import path

from ams.forum.views import forum_sso_login_callback
from ams.forum.views import forum_sso_login_redirect

app_name = "forum"
urlpatterns = [
    path("", forum_sso_login_redirect, name="forum-redirect"),
    path("sso", forum_sso_login_callback, name="forum-sso-login-callback"),
]
