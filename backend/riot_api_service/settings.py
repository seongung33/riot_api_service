"""Riot insight 백엔드의 Django 설정."""
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
# 로컬 개발 설정과 secret은 코드에 적지 않고 backend/.env에서 읽어온다.
load_dotenv(BASE_DIR / ".env")


# SECRET_KEY, DB 비밀번호, Riot API key는 환경변수에서 읽는다.
# 기본값은 개발 편의를 위한 값이며 실제 secret을 코드에 하드코딩하지 않는다.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes", "on"}

# 쉼표로 구분된 환경변수를 list로 바꿔 배포 환경마다 허용 host를 조정할 수 있게 한다.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    # 도메인 앱은 계정 식별, 매치 원본 저장, 분석 지표 계산, Riot API import 역할로 나뉜다.
    "accounts",
    "matches",
    "analytics",
    "riot_api",
]

MIDDLEWARE = [
    # 프론트 Vite 개발 서버에서 Django API를 호출할 수 있도록 CORS middleware를 가장 앞쪽에 둔다.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "riot_api_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "riot_api_service.wsgi.application"
ASGI_APPLICATION = "riot_api_service.asgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # DB 접속 정보는 환경변수에서 읽어 배포/로컬 환경을 코드 변경 없이 분리한다.
        "NAME": os.getenv("POSTGRES_DB", "riot_insight"),
        "USER": os.getenv("POSTGRES_USER", "riot_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    # API 응답은 JSON을 기본으로 사용하되, 개발 중 확인을 위해 Browsable API도 열어둔다.
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        # 현재 프론트는 JSON body로 검색 요청을 보내므로 JSONParser를 사용한다.
        "rest_framework.parsers.JSONParser",
    ],
}

CORS_ALLOWED_ORIGINS = [
    # 프론트 개발 서버 주소도 환경변수로 바꿀 수 있게 해 로컬/배포 설정을 분리한다.
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

# Riot API key와 route 설정은 환경변수에서 읽는다.
# key는 요청 헤더에만 사용하고 코드에 직접 출력하거나 저장하지 않는다.
RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")
RIOT_DEFAULT_REGION = os.getenv("RIOT_DEFAULT_REGION", "asia")
RIOT_DEFAULT_PLATFORM = os.getenv("RIOT_DEFAULT_PLATFORM", "kr")
