from django.urls import path


app_name = "matches"

# 현재 match 데이터는 accounts와 riot_api workflow를 통해 조회/저장된다.
# 독립적인 match detail API가 필요해지면 이 urlpatterns에 path를 추가한다.
urlpatterns = []
