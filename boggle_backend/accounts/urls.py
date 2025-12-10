from django.urls import path

from .views import (
    LoginVerifyView,
    LogoutView,
    DailyChallengeView,
    DailyLeaderboardView,
    ChallengeLeaderboardView,
    SessionRankView,
    UserStatsView,
    UserSettingsView,
    UserProfileView,
    SendChallengeView,
    WordDefinitionView,
)

urlpatterns = [
    path('auth/login/verify/', LoginVerifyView.as_view(), name='auth_login_verify'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('daily-challenge/', DailyChallengeView.as_view(), name='daily_challenge'),
    path('leaderboards/daily/', DailyLeaderboardView.as_view(), name='daily_leaderboard'),
    path('leaderboards/challenge/<int:challenge_id>/', ChallengeLeaderboardView.as_view(), name='challenge_leaderboard'),
    path('sessions/<int:pk>/rank/', SessionRankView.as_view(), name='session_rank'),
    path('stats/', UserStatsView.as_view(), name='user_stats'),
    path('settings/', UserSettingsView.as_view(), name='user_settings'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('challenges/<int:challenge_id>/send/', SendChallengeView.as_view(), name='challenge_send'),
    path('words/<str:word>/definition/', WordDefinitionView.as_view(), name='word_definition'),
]

