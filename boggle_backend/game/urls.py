from django.urls import path

from .views import (
    ChallengeCreateView,
    ChallengeMineView,
    ChallengeDeleteView,
    SessionCreateView,
    SessionSubmitWordView,
    SessionEndView,
)

# Dev A scan: new router for game-specific endpoints; legacy API routes live under api/urls.py.

urlpatterns = [
    path('challenges/', ChallengeCreateView.as_view(), name='game_challenges_create'),
    path('challenges/mine/', ChallengeMineView.as_view(), name='game_challenges_mine'),
    path('challenges/<int:pk>/', ChallengeDeleteView.as_view(), name='game_challenges_delete'),
    path('sessions/', SessionCreateView.as_view(), name='game_sessions_create'),
    path('sessions/<int:pk>/submit-word/', SessionSubmitWordView.as_view(), name='game_sessions_submit_word'),
    path('sessions/<int:pk>/end/', SessionEndView.as_view(), name='game_sessions_end'),
]
