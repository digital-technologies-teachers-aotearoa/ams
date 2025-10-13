from django.contrib import admin

from ams.memberships.forms import MembershipOptionForm
from ams.memberships.models import MembershipOption


@admin.register(MembershipOption)
class MembershipOptionAdmin(admin.ModelAdmin):
    form = MembershipOptionForm
