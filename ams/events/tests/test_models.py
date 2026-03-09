import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from ams.events.models import Event
from ams.events.models import Region
from ams.events.tests.factories import EventFactory
from ams.events.tests.factories import LocationFactory
from ams.events.tests.factories import RegionFactory
from ams.events.tests.factories import SeriesFactory
from ams.events.tests.factories import SessionFactory


@pytest.mark.django_db
class TestRegion:
    def test_str(self):
        region = RegionFactory(name="Canterbury region")
        assert str(region) == "Canterbury region"

    def test_ordering(self):
        r1 = RegionFactory(name="Zebra", order=0)
        r2 = RegionFactory(name="Alpha", order=0)
        r3 = RegionFactory(name="Mid", order=1)
        regions = list(Region.objects.all())
        # order=0 items come first (alphabetical), then order=1
        assert regions == [r2, r1, r3]


@pytest.mark.django_db
class TestLocation:
    def test_str_returns_full_address(self):
        region = RegionFactory(name="Canterbury region")
        location = LocationFactory(
            name="UC",
            room="Room 1",
            street_address="20 Kirkwood Ave",
            suburb="Ilam",
            city="Christchurch",
            region=region,
        )
        address = str(location)
        assert "Room 1" in address
        assert "UC" in address
        assert "20 Kirkwood Ave" in address
        assert "Ilam" in address
        assert "Christchurch" in address
        assert "Canterbury region" in address

    def test_get_full_address_no_region(self):
        location = LocationFactory(
            name="UC",
            room="",
            street_address="",
            suburb="",
            city="Christchurch",
            region=None,
        )
        address = location.get_full_address()
        assert "Christchurch" in address
        assert "Canterbury" not in address

    def test_get_absolute_url(self):
        location = LocationFactory()
        url = location.get_absolute_url()
        assert f"/events/location/{location.pk}/" == url


@pytest.mark.django_db
class TestSeries:
    def test_str(self):
        series = SeriesFactory(name="Workshop Series")
        assert str(series) == "Workshop Series"


@pytest.mark.django_db
class TestEvent:
    def test_str(self):
        event = EventFactory(name="Test Event")
        assert str(event) == "Test Event"

    def test_get_absolute_url(self):
        event = EventFactory(name="Test Event")
        url = event.get_absolute_url()
        assert f"/events/event/{event.pk}/" in url

    def test_get_short_name_with_series(self):
        series = SeriesFactory(abbreviation="WS")
        event = EventFactory(name="Day 1", series=series)
        assert event.get_short_name() == "WS: Day 1"

    def test_get_short_name_without_series(self):
        event = EventFactory(name="Standalone Event", series=None)
        assert event.get_short_name() == "Standalone Event"

    def test_location_summary_no_locations(self):
        event = EventFactory()
        assert event.location_summary() is None

    def test_location_summary_single_location(self):
        region = RegionFactory(name="Canterbury region")
        location = LocationFactory(city="Christchurch", region=region)
        event = EventFactory(locations=[location])
        assert event.location_summary() == "Christchurch, Canterbury region"

    def test_location_summary_multiple_locations(self):
        loc1 = LocationFactory()
        loc2 = LocationFactory()
        event = EventFactory(locations=[loc1, loc2])
        assert event.location_summary() == "Multiple locations"

    def test_has_ended_true(self):
        event = EventFactory(end=timezone.now() - timezone.timedelta(days=1))
        assert event.has_ended is True

    def test_has_ended_false(self):
        event = EventFactory(end=timezone.now() + timezone.timedelta(days=1))
        assert event.has_ended is False

    def test_has_ended_none(self):
        event = EventFactory(end=None)
        assert event.has_ended is False

    def test_update_datetimes(self):
        event = EventFactory()
        start_time = timezone.now() + timezone.timedelta(days=1)
        end_time = timezone.now() + timezone.timedelta(days=3)
        SessionFactory(event=event, start=start_time, end=end_time)
        event.update_datetimes()
        event.refresh_from_db()
        assert event.start == start_time
        assert event.end == end_time

    def test_update_datetimes_no_sessions(self):
        event = EventFactory()
        original_start = event.start
        event.update_datetimes()
        event.refresh_from_db()
        assert event.start == original_start

    def test_clean_invite_only_with_link_raises(self):
        event = EventFactory.build(
            registration_type=Event.RegistrationType.INVITE_ONLY,
            registration_link="https://example.com",
        )
        with pytest.raises(ValidationError):
            event.clean()

    def test_clean_register_without_link_raises(self):
        event = EventFactory.build(
            registration_type=Event.RegistrationType.REGISTER,
            registration_link="",
        )
        with pytest.raises(ValidationError):
            event.clean()

    def test_clean_invite_only_no_link_ok(self):
        event = EventFactory.build(
            registration_type=Event.RegistrationType.INVITE_ONLY,
            registration_link="",
        )
        event.clean()  # Should not raise


@pytest.mark.django_db
class TestSession:
    def test_str(self):
        session = SessionFactory(name="Session 1")
        assert str(session) == "Session 1"

    def test_clean_end_before_start_raises(self):
        start = timezone.now() + timezone.timedelta(days=1)
        end = start - timezone.timedelta(hours=1)
        session = SessionFactory.build(start=start, end=end)
        with pytest.raises(ValidationError):
            session.clean()

    def test_clean_valid_times_ok(self):
        start = timezone.now() + timezone.timedelta(days=1)
        end = start + timezone.timedelta(hours=1)
        session = SessionFactory.build(start=start, end=end)
        session.clean()  # Should not raise
