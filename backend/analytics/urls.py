from django.urls import path


app_name = "analytics"

# 분석 결과는 현재 accounts endpoint에서 함께 제공된다.
# 별도 리포트 화면이 생기면 analytics 전용 APIView를 이곳에 연결한다.
urlpatterns = []
