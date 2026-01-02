from django.urls import path

from ams.memberships.views import CreateIndividualMembershipView
from ams.memberships.views import CreateOrganisationMembershipView

app_name = "memberships"
urlpatterns = [
    path(
        "apply-individual/",
        CreateIndividualMembershipView.as_view(),
        name="apply-individual",
    ),
    path(
        "apply-organisation/<uuid:uuid>/",
        CreateOrganisationMembershipView.as_view(),
        name="apply-organisation",
    ),
]
