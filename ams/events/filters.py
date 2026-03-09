import django_filters
from django.utils.timezone import now

from ams.entities.models import Entity
from ams.events.models import Event
from ams.events.models import Region


class BaseEventFilter(django_filters.FilterSet):
    locations__region = django_filters.ModelChoiceFilter(
        queryset=Region.objects.all(),
        label="Region",
        empty_label="Show all",
    )
    accessible_online = django_filters.ChoiceFilter(
        choices=(
            ("1", "Yes"),
            ("0", "No"),
        ),
        empty_label="Show all",
    )
    organisers = django_filters.ModelChoiceFilter(
        queryset=Entity.objects.all(),
        label="Organiser",
        empty_label="Show all",
    )

    class Meta:
        model = Event
        fields = [
            "locations__region",
            "accessible_online",
            "organisers",
        ]


class UpcomingEventFilter(BaseEventFilter):
    @property
    def qs(self):
        return (
            super()
            .qs.filter(published=True, end__gte=now())
            .order_by("start")
            .prefetch_related("organisers", "locations", "sponsors")
            .select_related("series")
            .distinct()
        )


class PastEventFilter(BaseEventFilter):
    @property
    def qs(self):
        return (
            super()
            .qs.filter(published=True, end__lt=now())
            .order_by("-end")
            .prefetch_related("organisers", "locations", "sponsors")
            .select_related("series")
            .distinct()
        )
