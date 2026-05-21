"""계정 관련 API에서 요청 검증과 응답 변환을 담당하는 DRF serializer."""

from rest_framework import serializers

from .models import RiotAccount


class RiotAccountSerializer(serializers.ModelSerializer):
    """DB에 저장된 RiotAccount 모델을 API 응답 JSON으로 변환한다."""

    class Meta:
        model = RiotAccount
        # ModelSerializer는 모델 필드 정의를 기반으로 직렬화 구조를 만든다.
        # read_only_fields는 클라이언트가 만들거나 수정하면 안 되는 서버 관리 필드를 보호한다.
        fields = [
            "id",
            "puuid",
            "game_name",
            "tag_line",
            "region",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AccountSearchRequestSerializer(serializers.Serializer):
    """계정 검색/최근 매치 import 요청 body를 검증한다."""

    # APIView에서는 이 serializer의 is_valid()를 먼저 통과시켜야 한다.
    # 이렇게 하면 Riot API를 호출하기 전에 필수값, 기본값, 범위 제한을 한 곳에서 보장할 수 있다.
    game_name = serializers.CharField(max_length=100)
    tag_line = serializers.CharField(max_length=20, default="KR1")
    region = serializers.CharField(max_length=20, required=False, default="asia")
    count = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)
    queue = serializers.IntegerField(required=False, default=420, min_value=0)


class RecentMatchSerializer(serializers.Serializer):
    """프론트의 최근 경기 목록에 필요한 participant 중심 응답 구조."""

    # 이 serializer는 모델 인스턴스를 직접 받기보다 service가 만든 dict를 검증 가능한 응답 형태로 맞춘다.
    # match 정보와 participant 통계가 함께 보이도록 두 데이터의 필드를 한 행으로 평탄화한다.
    match_id = serializers.CharField()
    game_version = serializers.CharField()
    queue_id = serializers.IntegerField()
    game_start_time = serializers.DateTimeField()
    game_duration = serializers.IntegerField()
    champion_id = serializers.IntegerField()
    champion_name = serializers.CharField()
    individual_position = serializers.CharField()
    win = serializers.BooleanField()
    kills = serializers.IntegerField()
    deaths = serializers.IntegerField()
    assists = serializers.IntegerField()
    kda = serializers.FloatField()
    total_cs = serializers.IntegerField()
    gold_earned = serializers.IntegerField()
    vision_score = serializers.IntegerField()
    total_damage_dealt_to_champions = serializers.IntegerField()
    total_damage_taken = serializers.IntegerField()


class AccountSummarySerializer(serializers.Serializer):
    """최근 경기들을 집계한 계정 단위 요약 지표 응답 구조."""

    # 승률, 평균 KDA, 주 포지션처럼 여러 MatchParticipant를 모아 계산한 값은
    # DB 단일 모델과 1:1로 대응하지 않으므로 일반 Serializer로 응답 모양을 명시한다.
    account_id = serializers.IntegerField()
    puuid = serializers.CharField()
    game_name = serializers.CharField()
    tag_line = serializers.CharField()
    region = serializers.CharField()
    game_count = serializers.IntegerField()
    win_rate = serializers.FloatField()
    average_kda = serializers.FloatField()
    average_kills = serializers.FloatField()
    average_deaths = serializers.FloatField()
    average_assists = serializers.FloatField()
    average_cs = serializers.FloatField()
    average_gold = serializers.FloatField()
    average_vision_score = serializers.FloatField()
    main_position = serializers.CharField(allow_null=True)
    champion_pool = serializers.ListField(child=serializers.CharField())


class ChampionPerformanceSerializer(serializers.Serializer):
    """챔피언별 플레이 성과를 카드/테이블로 보여주기 위한 응답 구조."""

    # 챔피언 풀을 설명할 때는 단일 경기보다 챔피언별 경기 수, 승률, 평균 지표가 중요하다.
    champion_id = serializers.IntegerField()
    champion_name = serializers.CharField()
    game_count = serializers.IntegerField()
    win_rate = serializers.FloatField()
    average_kda = serializers.FloatField()
    average_cs = serializers.FloatField()
    average_gold = serializers.FloatField()
    average_vision_score = serializers.FloatField()
    positions = serializers.ListField(child=serializers.CharField())


class FeedbackSerializer(serializers.Serializer):
    """룰 기반 피드백 카드 응답 구조."""

    # category/metric/value는 어떤 지표 때문에 피드백이 생성됐는지 추적하기 위한 메타데이터이고,
    # interpretation/recommendation은 화면에서 사용자에게 바로 보여줄 설명 문장이다.
    category = serializers.CharField()
    metric = serializers.CharField()
    value = serializers.FloatField()
    interpretation = serializers.CharField()
    recommendation = serializers.CharField()
    target = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class PhaseMetricSerializer(serializers.Serializer):
    """라인전/오브젝트 등 phase metric을 최근 경기별로 보여주는 응답 구조."""

    # phase metric은 timeline에서 계산된 분석 결과이고, champion_name 같은 표시 정보는
    # MatchParticipant에서 가져오므로 service에서 조합한 dict를 이 serializer로 응답한다.
    match_id = serializers.CharField()
    game_start_time = serializers.DateTimeField()
    champion_id = serializers.IntegerField()
    champion_name = serializers.CharField()
    position = serializers.CharField()
    lane_cs_diff_10 = serializers.IntegerField(allow_null=True)
    lane_gold_diff_10 = serializers.IntegerField(allow_null=True)
    lane_xp_diff_10 = serializers.IntegerField(allow_null=True)
    death_before_14 = serializers.BooleanField()
    objective_death_count = serializers.IntegerField()
