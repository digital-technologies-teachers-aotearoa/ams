from http import HTTPStatus

import pytest
from django.utils import timezone

from ams.events.tests.factories import EventFactory
from ams.events.tests.factories import LocationFactory

pytestmark = pytest.mark.django_db


class TestHomeView:
    def test_get(self, client):
        response = client.get("/en/events/")
        assert response.status_code == HTTPStatus.OK

    def test_map_locations_in_context(self, client):
        location = LocationFactory()
        EventFactory(locations=[location])
        response = client.get("/en/events/")
        assert "map_locations" in response.context


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
