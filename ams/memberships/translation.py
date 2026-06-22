from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import register

from ams.memberships.models import MembershipOption


@register(MembershipOption)
class MembershipOptionTranslationOptions(TranslationOptions):
    fields = ("name", "description")
