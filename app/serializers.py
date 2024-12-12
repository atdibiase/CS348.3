from rest_framework import serializers
from .models import Team, Game

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'season', 'name', 'coach', 'city', 'wins', 'losses', 'win_percentage']

class GameSerializer(serializers.ModelSerializer):
    home_team = serializers.StringRelatedField()
    away_team = serializers.StringRelatedField()

    class Meta:
        model = Game
        fields = ['id', 'date', 'home_team', 'away_team', 'location', 'home_score', 'away_score', 'winner']
