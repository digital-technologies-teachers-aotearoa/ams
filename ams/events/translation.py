from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import register

from ams.events.models import Event
from ams.events.models import Location
from ams.events.models import Region
from ams.events.models import Series
from ams.events.models import Session


@register(Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Series)
class SeriesTranslationOptions(TranslationOptions):
    fields = ("name", "abbreviation", "description")


@register(Event)
class EventTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Session)
class SessionTranslationOptions(TranslationOptions):
    fields = ("name", "description")
