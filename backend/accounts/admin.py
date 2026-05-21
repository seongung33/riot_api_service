"""계정 모델을 Django admin에서 확인하기 위한 등록."""

from django.contrib import admin

from .models import RiotAccount


@admin.register(RiotAccount)
class RiotAccountAdmin(admin.ModelAdmin):
    # Riot ID와 PUUID를 함께 보여주면 API import 후 계정이 어떤 식별자로 저장됐는지 확인하기 쉽다.
    list_display = ("game_name", "tag_line", "region", "puuid", "updated_at")
    # 운영 중 특정 사용자 검색은 Riot ID 또는 PUUID로 이루어질 가능성이 높다.
    search_fields = ("game_name", "tag_line", "puuid")
    list_filter = ("region",)
    readonly_fields = ("created_at", "updated_at")
