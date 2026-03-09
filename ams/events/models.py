from autoslug import AutoSlugField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from tinymce.models import HTMLField

from ams.entities.models import Entity


class Region(models.Model):
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Custom sort order. When 0 (unset), falls back to alphabetical sort.",
    )

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Location(models.Model):
    room = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of room or space, for example: Room 134",
    )
    name = models.CharField(
        max_length=200,
        help_text="Name of location, for example: Middleton Grange School",
    )
    street_address = models.CharField(
        max_length=200,
        blank=True,
        help_text="Street address location, for example: 12 High Street",
    )
    suburb = models.CharField(
        max_length=200,
        blank=True,
        help_text="Suburb, for example: Riccarton",
    )
    city = models.CharField(
        max_length=200,
        help_text="Town or city, for example: Christchurch",
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    description = HTMLField(blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.get_full_address()

    def get_absolute_url(self):
        return reverse("events:location", kwargs={"pk": self.pk})

    def get_full_address(self):
        address = ""
        if self.room:
            address += self.room + ",\n"
        address += self.name + ",\n"
        if self.street_address:
            address += self.street_address + ",\n"
        if self.suburb:
            address += self.suburb + ", "
        address += self.city
        if self.region:
            address += ",\n" + self.region.name
        return address


class Series(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=30)
    description = HTMLField()
    logo = models.ImageField(
        blank=True,
        upload_to="events/series/",
        help_text="Logo will be displayed instead of name if provided.",
    )

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.name


class Event(models.Model):
    class RegistrationType(models.IntegerChoices):
        REGISTER = 1, _("Register to attend event")
        APPLY = 2, _("Apply to attend event")
        EXTERNAL = 3, _("Visit event website")
        INVITE_ONLY = 4, _("This event is invite only")

    name = models.CharField(max_length=200)
    description = HTMLField()
    slug = AutoSlugField(populate_from="get_short_name", always_update=False, null=True)
    published = models.BooleanField(default=False)
    show_schedule = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    registration_type = models.PositiveSmallIntegerField(
        choices=RegistrationType.choices,
        default=RegistrationType.REGISTER,
    )
    registration_link = models.URLField(blank=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    accessible_online = models.BooleanField(
        default=False,
        help_text="Select if this event can be attended online",
    )
    price = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency="NZD",
        default=0,
    )
    locations = models.ManyToManyField(
        Location,
        related_name="events",
        blank=True,
    )
    sponsors = models.ManyToManyField(
        Entity,
        related_name="sponsored_events",
        blank=True,
    )
    organisers = models.ManyToManyField(
        Entity,
        related_name="events",
        blank=True,
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
    )
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start", "end"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("events:event", kwargs={"pk": self.pk, "slug": self.slug})

    def update_datetimes(self):
        first_session = self.sessions.order_by("start").first()
        last_session = self.sessions.order_by("-end").first()
        if first_session and last_session:
            Event.objects.filter(pk=self.pk).update(
                start=first_session.start,
                end=last_session.end,
            )

    def get_short_name(self):
        if self.series:
            return f"{self.series.abbreviation}: {self.name}"
        return self.name

    def location_summary(self):
        locations = list(self.locations.all())
        if len(locations) > 1:
            return "Multiple locations"
        if locations:
            location = locations[0]
            region_name = location.region.name if location.region else ""
            return f"{location.city}, {region_name}"
        return None

    @property
    def has_ended(self):
        if self.end is None:
            return False
        return now() > self.end

    def clean(self):
        if (
            self.registration_type == self.RegistrationType.INVITE_ONLY
            and self.registration_link
        ):
            raise ValidationError(
                {
                    "registration_link": _(
                        "Registration link must be empty when event is set to invite "
                        ""
                        "only.",
                    ),
                },
            )
        if (
            self.registration_type != self.RegistrationType.INVITE_ONLY
            and not self.registration_link
        ):
            raise ValidationError(
                {
                    "registration_link": _(
                        "Registration link must be given when event is not set to "
                        "invite only.",
                    ),
                },
            )


class Session(models.Model):
    name = models.CharField(max_length=200)
    description = HTMLField(blank=True)
    url = models.URLField(blank=True)
    url_label = models.CharField(max_length=200, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    locations = models.ManyToManyField(
        Location,
        related_name="sessions",
        blank=True,
    )

    class Meta:
        ordering = ["start", "end", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.start and self.end and self.end <= self.start:
            raise ValidationError(_("Session end time must be after start time."))
