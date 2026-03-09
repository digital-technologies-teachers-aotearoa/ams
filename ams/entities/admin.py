from django.contrib import admin

from ams.entities.models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("name", "url")
    search_fields = ("name",)
