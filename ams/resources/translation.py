from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import register

from ams.resources.models import Resource
from ams.resources.models import ResourceCategory
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag


@register(ResourceCategory)
class ResourceCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(ResourceTag)
class ResourceTagTranslationOptions(TranslationOptions):
    fields = ("name", "abbreviation")


@register(Resource)
class ResourceTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(ResourceComponent)
class ResourceComponentTranslationOptions(TranslationOptions):
    fields = ("name",)
