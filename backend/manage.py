#!/usr/bin/env python
"""Django 관리 명령어를 실행하는 진입점."""
import os
import sys


def main() -> None:
    """DJANGO_SETTINGS_MODULE을 지정하고 Django CLI를 실행한다."""
    # manage.py 명령어가 어느 설정 파일을 사용할지 알려준다.
    # runserver, test, migrate 모두 이 값을 기준으로 프로젝트 설정을 로드한다.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "riot_api_service.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and available on your "
            "PYTHONPATH environment variable? Did you forget to activate a "
            "virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
