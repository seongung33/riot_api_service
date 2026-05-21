from django.apps import AppConfig


class MatchesConfig(AppConfig):
    # match/participant/timeline row는 import가 반복될수록 많아질 수 있어 BigAutoField를 기본값으로 둔다.
    default_auto_field = "django.db.models.BigAutoField"
    name = "matches"
