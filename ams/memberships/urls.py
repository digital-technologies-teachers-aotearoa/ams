from django.urls import path

from ams.memberships.views import CreateIndividualMembershipView

app_name = "memberships"
urlpatterns = [
    path("apply/", CreateIndividualMembershipView.as_view(), name="apply"),
]
