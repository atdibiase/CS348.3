from django.urls import path
from.views import BasketballGames, add_game, get_games, edit_game, delete_game, filter_games, get_teams, generate_report

urlpatterns = [
    path('', BasketballGames, name='homepage'),
    path('add-game/', add_game, name='add-game'),
    path('get-games/', get_games, name='get-games'),
    path('edit-game/<int:game_id>/', edit_game, name='edit-game'),
    path('delete-game/<int:game_id>/', delete_game, name='delete-game'),
    path('filter-games/', filter_games, name='filter-games'),
    path('get-teams/', get_teams, name='get-teams'),
    path('generate-report/', generate_report, name='generate-report'),
]
