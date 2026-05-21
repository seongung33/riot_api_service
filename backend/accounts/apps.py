from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # BigAutoField를 기본 PK로 사용해 계정 row가 늘어나도 id 범위가 넉넉하도록 한다.
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
