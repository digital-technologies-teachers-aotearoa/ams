from decimal import Decimal
from http import HTTPStatus

import pytest
from django.contrib.admin.utils import flatten_fieldsets
from django.urls import reverse

from ams.entities.tests.factories import EntityFactory
from ams.events.admin import LocationAdminForm
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


def _location_change_url(location):
    return reverse("admin:events_location_change", args=[location.pk])


def _location_post_data(location, **overrides):
    data = {
        "name_en": location.name,
        "name_mi": "",
        "room": location.room,
        "street_address": location.street_address,
        "suburb": location.suburb,
        "city": location.city,
        "region": location.region_id or "",
        "description_en": "",
        "description_mi": "",
        "coordinates_0": "" if location.latitude is None else location.latitude,
        "coordinates_1": "" if location.longitude is None else location.longitude,
    }
    data.update(overrides)
    return data


class TestLocationAdmin:
    def test_change_form_renders_map_picker(self, admin_client):
        location = LocationFactory()

        response = admin_client.get(_location_change_url(location))

        assert response.status_code == HTTPStatus.OK
        assert 'id="leaflet-picker-map"' in response.content.decode()
        assert "coordinates" in flatten_fieldsets(
            response.context["adminform"].fieldsets,
        )

    def test_change_form_prefills_existing_coordinates(self, admin_client):
        location = LocationFactory(
            latitude=Decimal("-41.286460"),
            longitude=Decimal("174.776236"),
        )

        response = admin_client.get(_location_change_url(location))

        content = response.content.decode()
        assert 'value="-41.286460"' in content
        assert 'value="174.776236"' in content

    def test_save_persists_picked_coordinates(self, admin_client):
        location = LocationFactory(latitude=None, longitude=None)
        data = _location_post_data(
            location,
            coordinates_0="-43.532",
            coordinates_1="172.636",
        )

        response = admin_client.post(_location_change_url(location), data)

        assert response.status_code == HTTPStatus.FOUND
        location.refresh_from_db()
        assert location.latitude == Decimal("-43.532")
        assert location.longitude == Decimal("172.636")

    def test_save_with_blank_coordinates_clears_them(self, admin_client):
        location = LocationFactory(
            latitude=Decimal("-41.286460"),
            longitude=Decimal("174.776236"),
        )
        data = _location_post_data(
            location,
            coordinates_0="",
            coordinates_1="",
        )

        response = admin_client.post(_location_change_url(location), data)

        assert response.status_code == HTTPStatus.FOUND
        location.refresh_from_db()
        assert location.latitude is None
        assert location.longitude is None

    def test_save_leaves_coordinates_alone_when_field_absent(self):
        location = LocationFactory(
            latitude=Decimal("-41.28"),
            longitude=Decimal("174.77"),
        )
        data = {
            "name": location.name,
            "room": location.room,
            "street_address": location.street_address,
            "suburb": location.suburb,
            "city": location.city,
            "region": location.region_id or "",
            "description": "",
            "coordinates_0": "0",
            "coordinates_1": "0",
        }
        form = LocationAdminForm(data=data, instance=location)

        assert form.is_valid(), form.errors
        del form.cleaned_data["coordinates"]
        form.save()

        location.refresh_from_db()
        assert location.latitude == Decimal("-41.28")
        assert location.longitude == Decimal("174.77")
