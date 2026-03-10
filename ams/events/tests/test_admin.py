from http import HTTPStatus

import pytest
from django.urls import reverse

from ams.entities.tests.factories import EntityFactory
from ams.events.models import Event
from ams.events.tests.factories import EventFactory
from ams.events.tests.factories import LocationFactory
from ams.events.tests.factories import SessionFactory

pytestmark = pytest.mark.django_db

CHANGELIST_URL = reverse("admin:events_event_changelist")


def _duplicate(admin_client, events):
    return admin_client.post(
        CHANGELIST_URL,
        {
            "action": "duplicate_events",
            "_selected_action": [e.pk for e in events],
        },
    )


class TestDuplicateEvents:
    def test_duplicate_creates_new_event(self, admin_client):
        event = EventFactory(name="Original Event")

        response = _duplicate(admin_client, [event])

        assert response.status_code == HTTPStatus.FOUND
        expected_events = 2
        assert Event.objects.count() == expected_events
        new_event = Event.objects.exclude(pk=event.pk).get()
        assert new_event.description == event.description

    def test_duplicate_creates_new_event_with_duplicate_suffix(self, admin_client):
        event = EventFactory(name="Original Event")

        response = _duplicate(admin_client, [event])

        assert response.status_code == HTTPStatus.FOUND
        new_event = Event.objects.exclude(pk=event.pk).get()
        assert new_event.name == "Original Event (Duplicate)"

    def test_duplicate_sets_published_false(self, admin_client):
        event = EventFactory(published=True)

        _duplicate(admin_client, [event])

        new_event = Event.objects.exclude(pk=event.pk).get()
        assert new_event.published is False

    def test_duplicate_copies_sessions_without_duplicate_suffix(self, admin_client):
        event = EventFactory()
        SessionFactory(event=event, name="Session 1")
        SessionFactory(event=event, name="Session 2")

        _duplicate(admin_client, [event])

        new_event = Event.objects.exclude(pk=event.pk).get()
        new_sessions = new_event.sessions.order_by("name")
        expected_events = 2
        assert new_sessions.count() == expected_events
        assert list(new_sessions.values_list("name", flat=True)) == [
            "Session 1",
            "Session 2",
        ]

    def test_duplicate_copies_m2m_relations(self, admin_client):
        location = LocationFactory()
        sponsor = EntityFactory()
        organiser = EntityFactory()
        event = EventFactory(
            locations=[location],
            organisers=[organiser],
        )
        event.sponsors.add(sponsor)

        _duplicate(admin_client, [event])

        new_event = Event.objects.exclude(pk=event.pk).get()
        assert list(new_event.locations.all()) == [location]
        assert list(new_event.sponsors.all()) == [sponsor]
        assert list(new_event.organisers.all()) == [organiser]

    def test_duplicate_copies_session_locations(self, admin_client):
        event = EventFactory()
        location = LocationFactory()
        session = SessionFactory(event=event)
        session.locations.add(location)

        _duplicate(admin_client, [event])

        new_event = Event.objects.exclude(pk=event.pk).get()
        new_session = new_event.sessions.get()
        assert list(new_session.locations.all()) == [location]

    def test_duplicate_multiple_events(self, admin_client):
        event1 = EventFactory(name="Event A")
        event2 = EventFactory(name="Event B")

        _duplicate(admin_client, [event1, event2])

        expected_events = 4
        assert Event.objects.count() == expected_events

    def test_duplicate_preserves_original(self, admin_client):
        event = EventFactory(name="Original", published=True)
        SessionFactory(event=event, name="Session 1")

        _duplicate(admin_client, [event])

        event.refresh_from_db()
        assert event.name == "Original"
        assert event.published is True
        assert event.sessions.count() == 1
        assert event.sessions.first().name == "Session 1"
