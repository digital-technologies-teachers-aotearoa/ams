from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import register

from ams.terms.models import Term
from ams.terms.models import TermVersion


@register(Term)
class TermTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(TermVersion)
class TermVersionTranslationOptions(TranslationOptions):
    fields = ("content",)
