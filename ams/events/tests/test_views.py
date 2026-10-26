import datetime
from http import HTTPStatus

import pytest
from django.test import RequestFactory
from django.utils import timezone
from django.utils import translation
from django.utils.formats import date_format

from ams.events.cache import event_map_cache_key
from ams.events.tests.factories import EventFactory
from ams.events.tests.factories import LocationFactory
from ams.events.views import HomeView

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.usefixtures("locmem_cache"),
]


class TestHomeView:
    def test_get(self, client):
        response = client.get("/en/events/")
        assert response.status_code == HTTPStatus.OK

    def test_map_locations_in_context(self, client):
        location = LocationFactory()
        EventFactory(locations=[location])
        response = client.get("/en/events/")
        assert "map_locations" in response.context

    def test_map_location_date_format(self, client):
        location = LocationFactory()
        start = timezone.now() + datetime.timedelta(days=10)
        EventFactory(
            locations=[location],
            start=start,
            end=start + datetime.timedelta(days=1),
        )
        response = client.get("/en/events/")
        event_date = response.context["map_locations"][0]["events"][0]["date"]
        assert event_date == date_format(start, "j M Y")

    def test_map_payload_is_cached_by_language(self, client, locmem_cache):
        location = LocationFactory()
        EventFactory(locations=[location])

        client.get("/en/events/")

        assert locmem_cache.get(event_map_cache_key("en")) is not None
        assert locmem_cache.get(event_map_cache_key("mi")) is None

        view = HomeView()
        view.setup(RequestFactory().get("/"))
        with translation.override("mi"):
            view.get_context_data()
        assert locmem_cache.get(event_map_cache_key("mi")) is not None

    def test_event_update_invalidates_cached_map(
        self,
        client,
        locmem_cache,
        django_capture_on_commit_callbacks,
    ):
        location = LocationFactory()
        event = EventFactory(locations=[location])
        client.get("/en/events/")
        cache_key = event_map_cache_key("en")
        assert locmem_cache.get(cache_key) is not None

        with django_capture_on_commit_callbacks(execute=True):
            event.name = "Updated event"
            event.save()

        assert locmem_cache.get(cache_key) is None

    def test_location_and_relationship_changes_invalidate_cached_map(
        self,
        client,
        locmem_cache,
        django_capture_on_commit_callbacks,
    ):
        location = LocationFactory()
        event = EventFactory(locations=[location])
        client.get("/en/events/")
        cache_key = event_map_cache_key("en")
        assert locmem_cache.get(cache_key) is not None

        with django_capture_on_commit_callbacks(execute=True):
            location.name = "Updated location"
            location.save()

        assert locmem_cache.get(cache_key) is None
        client.get("/en/events/")

        with django_capture_on_commit_callbacks(execute=True):
            event.locations.clear()

        assert locmem_cache.get(cache_key) is None

    @pytest.mark.skip(reason="Te Reo Māori translation required")
    def test_map_location_date_uses_active_language(self, rf):
        location = LocationFactory()
        start = datetime.datetime(2026, 7, 15, 0, 0, 0, tzinfo=datetime.UTC)
        EventFactory(
            locations=[location],
            start=start,
            end=start + datetime.timedelta(days=1),
        )
        request = rf.get("/en/events/")
        view = HomeView()
        view.setup(request)
        with translation.override("mi"):
            context = view.get_context_data()
        event_date = context["map_locations"][0]["events"][0]["date"]
        assert event_date == "15 Jul 2026"


class TestEventUpcomingView:
    def test_get(self, client):
        response = client.get("/en/events/upcoming/")
        assert response.status_code == HTTPStatus.OK

    def test_shows_future_events(self, client):
        future_event = EventFactory(
            published=True,
            start=timezone.now() + timezone.timedelta(days=1),
            end=timezone.now() + timezone.timedelta(days=2),
        )
        past_event = EventFactory(
            published=True,
            start=timezone.now() - timezone.timedelta(days=2),
            end=timezone.now() - timezone.timedelta(days=1),
        )
        response = client.get("/en/events/upcoming/")
        qs = response.context["filter"].qs
        assert future_event in qs
        assert past_event not in qs


class TestEventPastView:
    def test_get(self, client):
        response = client.get("/en/events/past/")
        assert response.status_code == HTTPStatus.OK


class TestEventDetailView:
    def test_get_with_slug(self, client):
        event = EventFactory(published=True)
        response = client.get(event.get_absolute_url())
        assert response.status_code == HTTPStatus.OK

    def test_redirect_without_slug(self, client):
        event = EventFactory(published=True)
        response = client.get(f"/en/events/event/{event.pk}/")
        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert event.get_absolute_url() in response.url

    def test_unpublished_event_404(self, client):
        event = EventFactory(published=False)
        response = client.get(event.get_absolute_url(), follow=True)
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestLocationDetailView:
    def test_get(self, client):
        location = LocationFactory()
        response = client.get(f"/en/events/location/{location.pk}/")
        assert response.status_code == HTTPStatus.OK
