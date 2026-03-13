from django.utils.timezone import now
from django.views import generic
from django_filters.views import FilterView

from ams.events.filters import PastEventFilter
from ams.events.filters import UpcomingEventFilter
from ams.events.models import Event
from ams.events.models import Location
from ams.events.utils import create_filter_helper
from ams.events.utils import organise_schedule_data
from ams.utils.mixins import RedirectToCosmeticURLMixin


class HomeView(generic.TemplateView):
    template_name = "events/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        future_events = (
            Event.objects.filter(published=True, end__gte=now())
            .order_by("start")
            .prefetch_related("organisers", "locations", "sponsors")
            .select_related("series")
        )
        raw_map_locations = {}
        for event in future_events:
            for location in event.locations.all():
                if location.latitude is None or location.longitude is None:
                    continue
                key = location.pk
                if key not in raw_map_locations:
                    raw_map_locations[key] = {
                        "coords": {
                            "lat": float(location.latitude),
                            "lng": float(location.longitude),
                        },
                        "title": location.name,
                        "events": [],
                    }
                raw_map_locations[key]["events"].append(
                    {
                        "url": event.get_absolute_url(),
                        "date": event.start.strftime("%-d %b %Y")
                        if event.start
                        else "",
                        "name": event.name,
                    },
                )
        context["map_locations"] = list(raw_map_locations.values())
        context["upcoming_events"] = future_events[:3]
        return context


class EventUpcomingView(FilterView):
    filterset_class = UpcomingEventFilter
    context_object_name = "events"
    template_name = "events/upcoming_events.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_formatter"] = create_filter_helper("events:upcoming")
        return context


class EventPastView(FilterView):
    filterset_class = PastEventFilter
    context_object_name = "events"
    template_name = "events/past_events.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_formatter"] = create_filter_helper("events:past")
        return context


class EventDetailView(RedirectToCosmeticURLMixin, generic.DetailView):
    model = Event
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.filter(published=True).prefetch_related("locations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sponsors"] = self.object.sponsors.all()
        context["organisers"] = self.object.organisers.all()
        context["schedule"] = organise_schedule_data(
            self.object.sessions.all().prefetch_related("locations"),
        )
        locations = self.object.locations.all()
        context["locations"] = locations
        context["event_markers"] = [
            {
                "coords": {
                    "lat": float(loc.latitude),
                    "lng": float(loc.longitude),
                },
                "title": loc.name,
                "text": "<br />" + loc.get_full_address().replace("\n", "<br />"),
            }
            for loc in locations
            if loc.latitude and loc.longitude
        ]
        context["map_zoom"] = 13 if locations.count() == 1 else 5
        return context


class LocationDetailView(RedirectToCosmeticURLMixin, generic.DetailView):
    model = Location
    context_object_name = "location"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upcoming_events"] = (
            Event.objects.filter(
                published=True,
                end__gte=now(),
                locations=self.object,
            )
            .order_by("start")
            .prefetch_related("organisers", "locations", "sponsors")
            .select_related("series")[:5]
        )
        loc = self.object
        if loc.latitude and loc.longitude:
            context["event_markers"] = [
                {
                    "coords": {
                        "lat": float(loc.latitude),
                        "lng": float(loc.longitude),
                    },
                    "title": loc.name,
                    "text": "<br />" + loc.get_full_address().replace("\n", "<br />"),
                },
            ]
        else:
            context["event_markers"] = []
        context["map_zoom"] = 18
        return context
