from django.urls import path

from .views import ChallengeCreateView

# Dev A scan: new router for game-specific endpoints; legacy API routes live under api/urls.py.

urlpatterns = [
    path('challenges/', ChallengeCreateView.as_view(), name='game_challenges_create'),
]
