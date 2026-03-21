import logging

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from ams.events.models import Event
from ams.events.models import Location
from ams.events.models import Region
from ams.events.models import Series
from ams.events.models import Session
from ams.events.widgets import LeafletPickerWidget

logger = logging.getLogger(__name__)


class EventsFeatureFlagMixin:
    """Hides events admin when EVENTS_ENABLED is False."""

    def has_module_permission(self, request):
        if not settings.EVENTS_ENABLED:
            return False
        return super().has_module_permission(request)

    def has_add_permission(self, request):
        if not settings.EVENTS_ENABLED:
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if not settings.EVENTS_ENABLED:
            return False
        return super().has_change_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        if not settings.EVENTS_ENABLED:
            return False
        return super().has_view_permission(request, obj)


class CoordinatesField(forms.MultiValueField):
    widget = LeafletPickerWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DecimalField(max_digits=9, decimal_places=6, required=False),
            forms.DecimalField(max_digits=9, decimal_places=6, required=False),
        )
        super().__init__(fields=fields, require_all_fields=False, *args, **kwargs)  # noqa: B026

    def compress(self, data_list):
        return data_list or [None, None]


class LocationAdminForm(forms.ModelForm):
    coordinates = CoordinatesField(required=False, label="Coordinates")

    class Meta:
        model = Location
        fields = [
            "name",
            "room",
            "street_address",
            "suburb",
            "city",
            "region",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["coordinates"].initial = [
                self.instance.latitude,
                self.instance.longitude,
            ]

    def save(self, commit=True):  # noqa: FBT002
        instance = super().save(commit=False)
        coords = self.cleaned_data.get("coordinates") or [None, None]
        instance.latitude = coords[0]
        instance.longitude = coords[1]
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Region)
class RegionAdmin(EventsFeatureFlagMixin, admin.ModelAdmin):
    list_display = ("name", "order")
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(EventsFeatureFlagMixin, admin.ModelAdmin):
    form = LocationAdminForm
    list_display = ("name", "room", "street_address", "suburb", "city", "region")
    list_filter = ("region",)
    search_fields = ("name", "room", "street_address", "suburb", "city")
    autocomplete_fields = ("region",)


class SessionInline(admin.StackedInline):
    model = Session
    fk_name = "event"
    extra = 3
    min_num = 1
    ordering = ("start", "end", "name")
    autocomplete_fields = ("locations",)


class EventUpcomingListFilter(admin.SimpleListFilter):
    title = _("time")
    parameter_name = "time"

    def lookups(self, request, model_admin):
        return (
            ("upcoming", _("Upcoming events")),
            ("past", _("Past events")),
            ("all", _("All events")),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = "upcoming"
        if self.value() == "upcoming":
            return queryset.filter(end__gte=now())
        if self.value() == "past":
            return queryset.filter(end__lt=now())
        return queryset

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup},
                ),
                "display": title,
            }


@admin.action(description="Duplicate selected events")
def duplicate_events(modeladmin, request, queryset):
    count = 0
    for event in queryset:
        # Store M2M relations and sessions before duplicating
        locations = list(event.locations.all())
        sponsors = list(event.sponsors.all())
        organisers = list(event.organisers.all())
        sessions = list(event.sessions.all())

        # Duplicate event
        event.pk = None
        event.id = None
        event.slug = None
        event.published = False
        event.name = f"{event.name} (Duplicate)"
        event.save()

        # Copy M2M relations
        event.locations.set(locations)
        event.sponsors.set(sponsors)
        event.organisers.set(organisers)

        # Duplicate sessions
        for session in sessions:
            session_locations = list(session.locations.all())
            session.pk = None
            session.id = None
            session.event = event
            session.save()
            session.locations.set(session_locations)

        event.update_datetimes()
        count += 1

    modeladmin.message_user(request, f"Successfully duplicated {count} event(s).")


@admin.register(Event)
class EventAdmin(EventsFeatureFlagMixin, admin.ModelAdmin):
    model = Event
    inlines = [SessionInline]
    actions = [duplicate_events]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "series",
                    "organisers",
                    "sponsors",
                    "price",
                ),
            },
        ),
        (
            "Location",
            {
                "fields": ("accessible_online", "locations"),
            },
        ),
        (
            "Registration",
            {
                "description": "Currently only registration via URL is available.",
                "fields": (
                    "registration_link",
                    "registration_type",
                ),
            },
        ),
        (
            "Visibility",
            {
                "fields": (
                    "published",
                    "featured",
                    "show_schedule",
                ),
            },
        ),
    )
    filter_horizontal = ("organisers", "sponsors")
    list_display = (
        "name",
        "location_summary",
        "series",
        "start",
        "end",
        "published",
        "featured",
    )
    list_filter = (EventUpcomingListFilter, "organisers")
    ordering = ("start", "end", "name")
    autocomplete_fields = ("locations",)
    save_on_top = True

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.update_datetimes()


@admin.register(Series)
class SeriesAdmin(EventsFeatureFlagMixin, admin.ModelAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name",)
