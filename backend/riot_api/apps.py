from django.apps import AppConfig


class RiotApiConfig(AppConfig):
    # Riot API workflow 앱은 현재 모델이 거의 없지만 프로젝트 전체 PK 정책과 맞춘다.
    default_auto_field = "django.db.models.BigAutoField"
    name = "riot_api"
