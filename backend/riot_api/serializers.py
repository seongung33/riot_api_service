"""Riot API import endpoint의 요청/응답 구조를 정의하는 serializer."""

from rest_framework import serializers


class ImportRecentMatchesRequestSerializer(serializers.Serializer):
    """최근 매치 import 요청 body를 검증한다."""

    # count와 queue 범위를 serializer에서 제한해 외부 Riot API 호출 전에 잘못된 요청을 걸러낸다.
    game_name = serializers.CharField(max_length=100)
    tag_line = serializers.CharField(max_length=20)
    region = serializers.CharField(max_length=20, required=False, default="asia")
    count = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)
    queue = serializers.IntegerField(required=False, default=420, min_value=0)


class ImportRecentMatchesResponseSerializer(serializers.Serializer):
    """최근 매치 import 결과를 프론트/테스트가 읽기 쉬운 구조로 변환한다."""

    # requested_count와 imported_match_ids를 함께 내려주면
    # 사용자가 요청한 경기 수와 실제 저장된 경기 목록을 비교할 수 있다.
    account_id = serializers.IntegerField()
    puuid = serializers.CharField()
    game_name = serializers.CharField()
    tag_line = serializers.CharField()
    region = serializers.CharField()
    requested_count = serializers.IntegerField()
    imported_match_ids = serializers.ListField(child=serializers.CharField())
