from django.urls import path

from .views import ChallengeCreateView, ChallengeMineView, ChallengeDeleteView

# Dev A scan: new router for game-specific endpoints; legacy API routes live under api/urls.py.

urlpatterns = [
    path('challenges/', ChallengeCreateView.as_view(), name='game_challenges_create'),
    path('challenges/mine/', ChallengeMineView.as_view(), name='game_challenges_mine'),
    path('challenges/<int:pk>/', ChallengeDeleteView.as_view(), name='game_challenges_delete'),
]
