from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    # 분석 지표 row도 경기 수에 비례해 늘어나므로 Django 기본 BigAutoField 정책을 명시한다.
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"
