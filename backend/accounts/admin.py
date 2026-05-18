"""Admin registrations for accounts."""

from django.contrib import admin

from .models import RiotAccount


@admin.register(RiotAccount)
class RiotAccountAdmin(admin.ModelAdmin):
    list_display = ("game_name", "tag_line", "region", "puuid", "updated_at")
    search_fields = ("game_name", "tag_line", "puuid")
    list_filter = ("region",)
    readonly_fields = ("created_at", "updated_at")
