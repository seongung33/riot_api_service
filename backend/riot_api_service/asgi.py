"""riot_api_service 프로젝트의 ASGI 설정."""
import os

from django.core.asgi import get_asgi_application


# 비동기 서버가 Django 앱을 로드할 때 사용할 설정 모듈을 지정한다.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "riot_api_service.settings")

# Daphne/Uvicorn 같은 ASGI 서버가 이 application 객체를 진입점으로 사용한다.
application = get_asgi_application()
