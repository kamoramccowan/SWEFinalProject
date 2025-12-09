from django.urls import path

from .views import (
    ChallengeCreateView,
    ChallengeMineView,
    ChallengeDeleteView,
    ChallengeShuffleView,
    ChallengeRotateView,
    ChallengeBySlugView,
    SessionCreateView,
    SessionSubmitWordView,
    SessionEndView,
    SessionResultsView,
    SessionHintView,
)

# Dev A scan: new router for game-specific endpoints; legacy API routes live under api/urls.py.

urlpatterns = [
    path('challenges/', ChallengeCreateView.as_view(), name='game_challenges_create'),
    path('challenges/mine/', ChallengeMineView.as_view(), name='game_challenges_mine'),
    path('challenges/<int:pk>/', ChallengeDeleteView.as_view(), name='game_challenges_delete'),
    path('challenges/<int:pk>/shuffle/', ChallengeShuffleView.as_view(), name='game_challenges_shuffle'),
    path('challenges/<int:pk>/rotate/', ChallengeRotateView.as_view(), name='game_challenges_rotate'),
    path('challenges/by-slug/<slug:share_slug>/', ChallengeBySlugView.as_view(), name='game_challenges_by_slug'),
    path('sessions/', SessionCreateView.as_view(), name='game_sessions_create'),
    path('sessions/<int:pk>/submit-word/', SessionSubmitWordView.as_view(), name='game_sessions_submit_word'),
    path('sessions/<int:pk>/end/', SessionEndView.as_view(), name='game_sessions_end'),
    path('sessions/<int:pk>/results/', SessionResultsView.as_view(), name='game_sessions_results'),
    path('sessions/<int:pk>/hint/', SessionHintView.as_view(), name='game_sessions_hint'),
]
