from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import FirebaseAuthentication
from .permissions import IsAuthenticatedFirebaseUser
from .serializers import AuthenticatedUserSerializer, UserSettingsSerializer
from .daily import get_or_create_daily_challenge
from datetime import date
from .leaderboards import get_daily_leaderboard, get_challenge_leaderboard, compute_session_rank, milestone_for_rank
from django.utils import timezone
from game.models import GameSession, Challenge
from .stats import compute_user_stats
from accounts.models import UserSettings, ChallengeInvite, User
from accounts.privacy import can_receive_challenge
from accounts.mail import send_challenge_email
from django.conf import settings

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


class UserStatsView(APIView):
    """
    Return aggregated stats for the authenticated user (FR-16).
    """
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def get(self, request):
        stats = compute_user_stats(request.user.id)
        return Response({"stats": stats}, status=status.HTTP_200_OK)


class UserSettingsView(APIView):
    """
    Read/update user privacy settings (FR-18).
    """
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def get(self, request):
        settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)

    def _update(self, request):
        settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"error_code": "VALIDATION_ERROR", "message": "Invalid settings payload.", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SendChallengeView(APIView):
    """
    Targeted send of a challenge to another user, enforcing recipient privacy (FR-18).
    """
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def post(self, request, challenge_id):
        target_user_id = request.data.get("target_user_id")
        if not target_user_id:
            return Response(
                {"error_code": "VALIDATION_ERROR", "message": "target_user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            recipient = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response(
                {"error_code": "TARGET_NOT_FOUND", "message": "Recipient user not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Privacy enforcement
        if not can_receive_challenge(recipient, sender=request.user):
            return Response(
                {"error_code": "PRIVACY_BLOCKED", "message": "Recipient does not accept incoming challenges."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            challenge = Challenge.objects.active().get(pk=challenge_id)
        except Exception:
            return Response(
                {"error_code": "CHALLENGE_NOT_FOUND", "message": "Challenge not found or unavailable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        invite = ChallengeInvite.objects.create(
            challenge=challenge,
            sender=request.user,
            recipient=recipient,
        )
        share_link = self._build_share_link(challenge)
        email_sent = False
        if recipient.email:
            email_sent = send_challenge_email(
                recipient.email,
                share_link,
                sender_name=request.user.display_name or request.user.username or "",
                challenge_title=challenge.title,
            )
        else:
            # If recipient lacks email, surface a clear message.
            return Response(
                {"error_code": "RECIPIENT_NO_EMAIL", "message": "Recipient has no email on file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": invite.id,
                "challenge_id": challenge.id,
                "recipient_id": recipient.id,
                "sender_id": request.user.id,
                "created_at": invite.created_at,
                "status": "sent",
                "email_sent": bool(email_sent),
                "share_link": share_link,
            },
            status=status.HTTP_201_CREATED,
        )

    def _build_share_link(self, challenge):
        base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:3000")
        slug = getattr(challenge, "share_slug", "")
        if slug:
            return f"{base}/challenges/{slug}"
        return f"{base}/challenges/{challenge.id}"
