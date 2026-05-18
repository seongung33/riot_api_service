"""DRF serializers for Riot API integration endpoints."""

from rest_framework import serializers


class ImportRecentMatchesRequestSerializer(serializers.Serializer):
    """Request body for importing a player's recent Riot matches."""

    game_name = serializers.CharField(max_length=100)
    tag_line = serializers.CharField(max_length=20)
    region = serializers.CharField(max_length=20, required=False, default="asia")
    count = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)
    queue = serializers.IntegerField(required=False, default=420, min_value=0)


class ImportRecentMatchesResponseSerializer(serializers.Serializer):
    """Response body for a recent match import run."""

    account_id = serializers.IntegerField()
    puuid = serializers.CharField()
    game_name = serializers.CharField()
    tag_line = serializers.CharField()
    region = serializers.CharField()
    requested_count = serializers.IntegerField()
    imported_match_ids = serializers.ListField(child=serializers.CharField())
