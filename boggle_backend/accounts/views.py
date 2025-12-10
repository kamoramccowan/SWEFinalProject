from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import FirebaseAuthentication
from .permissions import IsAuthenticatedFirebaseUser
from .serializers import AuthenticatedUserSerializer
from .daily import get_or_create_daily_challenge
from datetime import date
from .leaderboards import get_daily_leaderboard, get_challenge_leaderboard, compute_session_rank, milestone_for_rank
from django.utils import timezone
from game.models import GameSession

# Dev B scan (FR-01): No existing auth endpoints or custom User model; project relies on Django's default user with no Firebase integration.
# Plan: add an accounts app with a custom User storing firebase_uid/display_name, a FirebaseAuthentication backend, a permission guard,
# and login verification / logout endpoints for Firebase-backed clients.


class LoginVerifyView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def post(self, request):
        serializer = AuthenticatedUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def post(self, request):
        # Firebase logout is client-side; backend simply acknowledges and could clear server-side session if added.
        return Response(
            {
                "message": "Logout acknowledged. Firebase sessions are client-managed; no server token state to revoke.",
            },
            status=status.HTTP_200_OK,
        )


class DailyChallengeView(APIView):
    """
    Return today's daily challenge (lazy create if not set).
    """

    def get(self, request):
        today = date.today()
        try:
            daily = get_or_create_daily_challenge(today)
        except ValueError as exc:
            return Response(
                {"error_code": "NO_ACTIVE_CHALLENGES", "message": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        challenge = daily.challenge
        payload = {
            "date": str(daily.date),
            "challenge_id": challenge.id,
            "title": challenge.title,
            "difficulty": challenge.difficulty,
            "grid": challenge.grid,
            "share_slug": getattr(challenge, "share_slug", None),
            "created_at": challenge.created_at,
        }
        return Response(payload, status=status.HTTP_200_OK)


class DailyLeaderboardView(APIView):
    """
    Return today's daily leaderboard (top scores) (FR-15).
    """

    def get(self, request):
        today = date.today()
        try:
            challenge_id, entries = get_daily_leaderboard(today)
        except ValueError as exc:
            return Response(
                {"error_code": "NO_ACTIVE_CHALLENGES", "message": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "challenge_id": challenge_id,
                "entries": entries,
                "last_updated": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class ChallengeLeaderboardView(APIView):
    """
    Return leaderboard for a specific challenge (FR-15).
    """

    def get(self, request, challenge_id):
        entries = get_challenge_leaderboard(challenge_id)
        return Response(
            {
                "challenge_id": challenge_id,
                "entries": entries,
                "last_updated": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class SessionRankView(APIView):
    """
    Return rank for a specific session (FR-15).
    """

    def get(self, request, pk):
        try:
            session = GameSession.objects.select_related('challenge').get(pk=pk)
        except GameSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        rank_info = {
            "rank": None,
            "total_players": 0,
        }
        # Only compute rank for challenge mode with an owner
        if session.mode == GameSession.MODE_CHALLENGE and session.end_time:
            from accounts.leaderboards import compute_session_rank
            rank_info = compute_session_rank(session)

        return Response(rank_info, status=status.HTTP_200_OK)
