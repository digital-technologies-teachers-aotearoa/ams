from django.urls import path

from .views import individual_registration

urlpatterns = [
    path("individual-registration/", individual_registration, name="individual-registration"),
]
