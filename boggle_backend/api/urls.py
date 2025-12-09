from django.urls import path

from .views import (
    challenge_detail,
    challenges,
    create_game,
    generate_dictionary,
    get_game,
    get_games,
)

urlpatterns = [
    path('challenges/', challenges, name='challenges'),
    path('challenges/<int:pk>/', challenge_detail, name='challenge_detail'),
    path('challenges/generate-dictionary/', generate_dictionary, name='generate_dictionary'),
    path('game/<int:pk>', get_game, name='get_game'),
    path('games/', get_games, name='get_games'),
    path('game/create/<int:size>', create_game, name='create_game')
]
