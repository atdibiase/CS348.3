import json
from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Team, Game
from .serializers import TeamSerializer, GameSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db import connection

def BasketballGames(request):
    return render(request, 'BasketballGames.html')

def get_games(request):
    games = Game.objects.all().order_by('id')  
    data = [
        {
            "game_id": game.id,
            "date": game.date,
            "home_team": game.home_team.name,
            "away_team": game.away_team.name,
            "location": game.location,
            "home_score": game.home_score,
            "away_score": game.away_score,
            "winner": game.winner,
        }
        for index, game in enumerate(games)
    ]
    return JsonResponse(data, safe=False)

def get_teams(request):
    teams = Team.objects.values('name').distinct()
    response_data = []
    for team in teams:
        team_name = team['name']
        seasons = Team.objects.filter(name=team_name).values_list('season', flat=True)
        response_data.append({
            'name': team_name,
            'seasons': list(seasons),
        })
    return JsonResponse(response_data, safe=False)

@csrf_exempt
def add_game(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO app_game (date, home_team_id, away_team_id, location, home_score, away_score)
                    VALUES (%s, %s, %s, (SELECT city FROM app_team WHERE id = %s), %s, %s)
                """, [
                    data['date'],
                    data['home_team_id'],
                    data['away_team_id'],
                    data['home_team_id'],  
                    data['home_score'],
                    data['away_score']
                ])
            return JsonResponse({'message': 'Game added successfully!'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def edit_game(request, game_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            game = Game.objects.get(pk=game_id)
            game.date = data['date']
            game.home_team_id = data['home_team_id']
            game.away_team_id = data['away_team_id']
            game.home_score = data['home_score']
            game.away_score = data['away_score']
            game.save()
            return JsonResponse({'message': 'Game updated successfully!'}, status=200)
        except Game.DoesNotExist:
            return JsonResponse({'error': 'Game not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def delete_game(request, game_id):
    if request.method == 'DELETE':
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM app_game WHERE id = %s", [game_id])
            return JsonResponse({'message': 'Game deleted successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def filter_games(request):
    if request.method == 'POST':
        try:
            filters = json.loads(request.body)
            query = Q()
            if filters.get('start_date') and filters.get('end_date'):
                query &= Q(date__range=[filters['start_date'], filters['end_date']])
            if filters.get('game_id_start') and filters.get('game_id_end'):
                query &= Q(id__range=[filters['game_id_start'], filters['game_id_end']])
            if filters.get('team_name'):
                query &= Q(home_team__name__icontains=filters['team_name']) | Q(away_team__name__icontains=filters['team_name'])
            if filters.get('team_season'):
                query &= Q(home_team__season__icontains=filters['team_season']) | Q(away_team__season__icontains=filters['team_season'])
            games = Game.objects.filter(query)
            data = [
                {
                    "game_id": game.id,
                    "date": game.date.strftime('%d-%m-%Y'),
                    "home_team": game.home_team.name,
                    "away_team": game.away_team.name,
                    "location": game.location,
                    "home_score": game.home_score,
                    "away_score": game.away_score,
                }
                for game in games
            ]
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def generate_report(request):
    if request.method == 'POST':
        try:
            filters = json.loads(request.body)
            games = Game.objects.select_related('home_team', 'away_team')
            if filters.get('start_date') and filters.get('end_date'):
                games = games.filter(date__range=[filters['start_date'], filters['end_date']])
            if filters.get('game_id_start') and filters.get('game_id_end'):
                games = games.filter(id__range=[filters['game_id_start'], filters['game_id_end']])
            if filters.get('team_name'):
                games = games.filter(
                    Q(home_team__name__icontains=filters['team_name']) |
                    Q(away_team__name__icontains=filters['team_name'])
                )
            if filters.get('team_season'):
                games = games.filter(
                    Q(home_team__season=filters['team_season']) |
                    Q(away_team__season=filters['team_season'])
                )
            if not games.exists():
                return JsonResponse({"error": "No games found for the given filters."}, status=400)
            team_ids = set()
            for game in games:
                team_ids.add(game.home_team.id)
                team_ids.add(game.away_team.id)
            teams = Team.objects.filter(id__in=team_ids)
            if not teams.exists():
                return JsonResponse({"error": "No teams found for the filtered games."}, status=400)
            team_stats = []
            for team in teams:
                wins = 0
                losses = 0
                for game in games:
                    if game.home_team == team:
                        if game.home_score > game.away_score:
                            wins += 1
                        elif game.home_score < game.away_score:
                            losses += 1
                    elif game.away_team == team:
                        if game.away_score > game.home_score:
                            wins += 1
                        elif game.away_score < game.home_score:
                            losses += 1
                win_percentage = (wins / (wins + losses)) if (wins + losses) > 0 else 0.0
                team_stats.append({
                    "id": team.id,
                    "name": team.name,
                    "season": team.season,
                    "coach": team.coach,
                    "city": team.city,
                    "wins": wins,
                    "losses": losses,
                    "win_percentage": win_percentage,
                })
            team_stats.sort(key=lambda x: (-x['wins'], -x['win_percentage']))
            for idx, team in enumerate(team_stats, start=1):
                team['ranking'] = idx
            filtered_games = [
                {
                    "game_id": game.id,
                    "date": game.date.strftime('%d-%m-%Y'),
                    "home_team": game.home_team.name,
                    "away_team": game.away_team.name,
                    "location": game.location,
                    "home_score": game.home_score,
                    "away_score": game.away_score,
                }
                for game in games
            ]
            return JsonResponse({"filtered_games": filtered_games, "teams": team_stats}, safe=False)
        except Exception as e:
            print("Error in generate_report:", str(e))
            return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

class TeamListCreateView(generics.ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class GameListCreateView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

class GameDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

class TeamWinPercentageView(APIView):
    def get(self, request, pk):
        team = Team.objects.get(pk=pk)
        if team.wins + team.losses > 0:
            win_percentage = team.wins / (team.wins + team.losses)
        else:
            win_percentage = 0.0
        return Response({"team": team.name, "win_percentage": win_percentage})

