"""URL configuration for terms app."""

from django.urls import path

from ams.terms import views

app_name = "terms"
urlpatterns = [
    path("", views.terms_list_view, name="list"),
    path("accept/", views.accept_terms_view, name="accept"),
]
