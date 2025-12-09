from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Challenge, GameSession
from .boggle_engine import get_valid_words, is_word_on_board, score_word, meets_min_length
from .serializers import (
    ChallengeSerializer,
    ChallengeListSerializer,
    GameSessionSerializer,
    SessionSubmitWordSerializer,
    SessionResultsSerializer,
)
from .hints import choose_hint
from .practice import create_practice_challenge
from .difficulty import get_difficulty_config
from .board_transforms import shuffle_grid, rotate_grid
from .slug_utils import generate_share_slug

# Dev A scan (FR-02): No game endpoints existed; legacy challenge endpoints are in api/views.py.
# Plan for FR-03: Add a "my challenges" listing that filters by authenticated user and reuses the Challenge model with a slim serializer.
# Plan for FR-04: Add delete (soft-delete) endpoint; ensure only creators can delete and deleted challenges are excluded from listings.
# Plan for FR-05: Add session creation endpoint for playing active challenges (mode=challenge).
# Plan for FR-06: Add one-word submission and end-session endpoints with timing checks.
# Plan for FR-09: Add practice mode to sessions without requiring a pre-existing challenge (generate board + valid words).


class ChallengeCreateView(APIView):
    """
    Create a new challenge using the authenticated user's id as creator_user_id.
    """

    def post(self, request):
        serializer = ChallengeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            challenge = serializer.save()
            return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)

        return Response(
            {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid challenge payload.",
                "details": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChallengeMineView(ListAPIView):
    """
    List challenges created by the authenticated user (FR-03).
    """

    serializer_class = ChallengeListSerializer

    def get_queryset(self):
        user_id = self._get_user_id()
        if not user_id:
            return Challenge.objects.none()
        return Challenge.objects.filter(
            creator_user_id=str(user_id),
            status=Challenge.STATUS_ACTIVE,
        ).order_by('-created_at')

    def _get_user_id(self):
        request = self.request
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None


class ChallengeDeleteView(APIView):
    """
    Soft-delete a challenge owned by the authenticated user (FR-04).
    """

    def delete(self, request, pk):
        challenge = get_object_or_404(Challenge.objects.active(), pk=pk)
        user_id = self._get_user_id(request)
        if not user_id or challenge.creator_user_id != str(user_id):
            return Response(
                {
                    "error_code": "FORBIDDEN",
                    "message": "You are not allowed to delete this challenge.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        challenge.status = Challenge.STATUS_DELETED
        challenge.save(update_fields=['status', 'updated_at'])
        return Response({"status": "deleted"}, status=status.HTTP_200_OK)

    def _get_user_id(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None


class SessionCreateView(APIView):
    """
    Start a game session for an active challenge (FR-05) or practice mode (FR-09).
    """

    def post(self, request):
        mode = (request.data.get('mode') or GameSession.MODE_CHALLENGE).lower()
        if mode == GameSession.MODE_PRACTICE:
            user_id = self._get_user_id(request)
            difficulty = request.data.get('difficulty') or "easy"
            practice_challenge = create_practice_challenge(difficulty, user_id)
            cfg = get_difficulty_config(practice_challenge.difficulty)
            session = GameSession.objects.create(
                challenge=practice_challenge,
                player_user_id=user_id,
                mode=GameSession.MODE_PRACTICE,
                duration_seconds=cfg["duration_seconds"] if cfg else None,
            )
            return Response(GameSessionSerializer(session).data, status=status.HTTP_201_CREATED)

        serializer = GameSessionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            session = serializer.save()
            return Response(
                GameSessionSerializer(session).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid session payload.",
                "details": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _get_user_id(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None


class ChallengeTransformMixin:
    def _get_active_challenge(self, pk):
        return get_object_or_404(Challenge.objects.active(), pk=pk)

    def _challenge_response(self, grid):
        # TODO: Recompute dictionary for transformed grids if needed for gameplay.
        return {"grid": grid}


class ChallengeBySlugView(APIView):
    """
    Fetch an active challenge by its shareable slug (FR-11).
    """

    def get(self, request, share_slug):
        challenge = get_object_or_404(Challenge.objects.active(), share_slug=share_slug)
        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_200_OK)


class ChallengeShuffleView(APIView, ChallengeTransformMixin):
    """
    Return a shuffled grid for an active challenge (FR-12).
    """

    def post(self, request, pk):
        challenge = self._get_active_challenge(pk)
        session_id = request.data.get('session_id')
        if session_id:
            session = get_object_or_404(GameSession.objects.select_related('challenge'), pk=session_id, challenge=challenge)
            if not self._is_owner_or_guest(session, request):
                return Response(
                    {"error_code": "FORBIDDEN", "message": "You cannot shuffle this session."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if session.shuffle_uses >= 2:
                return Response(
                    {"error_code": "SHUFFLE_LIMIT_REACHED", "message": "Shuffle limit reached for this session."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            session.shuffle_uses += 1
            session.save(update_fields=['shuffle_uses'])

        shuffled = shuffle_grid(challenge.grid)
        return Response(self._challenge_response(shuffled), status=status.HTTP_200_OK)

    def _is_owner_or_guest(self, session, request):
        if session.player_user_id is None:
            return True
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk) == session.player_user_id
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id) == session.player_user_id
        return False


class ChallengeRotateView(APIView, ChallengeTransformMixin):
    """
    Return a rotated grid for an active challenge (FR-12).
    """

    def post(self, request, pk):
        challenge = self._get_active_challenge(pk)
        angle = request.data.get('angle', 90)
        direction = request.data.get('direction', 'clockwise')
        try:
            angle_int = int(angle)
            rotated = rotate_grid(challenge.grid, direction=direction, angle=angle_int)
        except Exception as exc:
            return Response(
                {"error_code": "VALIDATION_ERROR", "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self._challenge_response(rotated), status=status.HTTP_200_OK)

    def _is_owner_or_guest(self, session, request):
        if session.player_user_id is None:
            return True
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk) == session.player_user_id
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id) == session.player_user_id
        return False

    def _get_user_id(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None


class SessionSubmitWordView(APIView):
    """
    Submit a single word to an active session (FR-06).
    """

    def post(self, request, pk):
        session = get_object_or_404(GameSession.objects.select_related('challenge'), pk=pk)

        if not self._is_owner_or_guest(session, request):
            return Response(
                {"error_code": "FORBIDDEN", "message": "You cannot submit to this session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.is_time_up():
            if not session.end_time:
                session.end_time = session.start_time + timezone.timedelta(seconds=session.duration_seconds or 0)
                session.save(update_fields=['end_time'])
            return Response(
                {"error_code": "TIME_UP", "message": "Session has ended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SessionSubmitWordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_code": "VALIDATION_ERROR", "message": "Invalid submission.", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        word = serializer.validated_data['word']
        word_norm = word.strip().upper()
        valid_set = get_valid_words(session.challenge)
        is_valid = (
            word_norm in valid_set
            and meets_min_length(word_norm, session.challenge.difficulty)
            and is_word_on_board(session.challenge.grid, word_norm)
        )
        score_delta = score_word(word_norm) if is_valid else 0

        submissions = list(session.submissions)
        submissions.append(
            {
                "word": word_norm,
                "is_valid": is_valid,
                "score_delta": score_delta,
                "timestamp": timezone.now().isoformat(),
            }
        )
        session.submissions = submissions
        if is_valid:
            session.score = (session.score or 0) + score_delta
            session.save(update_fields=['submissions', 'score'])
        else:
            session.save(update_fields=['submissions'])

        return Response(
            {
                "status": "accepted",
                "word": word_norm,
                "session_id": session.id,
                "is_valid": is_valid,
                "score_delta": score_delta,
                "score": session.score,
            },
            status=status.HTTP_200_OK,
        )

    def _is_owner_or_guest(self, session, request):
        if session.player_user_id is None:
            return True
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk) == session.player_user_id
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id) == session.player_user_id
        return False


class SessionResultsView(APIView):
    """
    Return all valid words, found words, and final score for an ended session (FR-08).
    """

    def get(self, request, pk):
        session = get_object_or_404(GameSession.objects.select_related('challenge'), pk=pk)

        if not self._is_owner_or_guest(session, request):
            return Response(
                {"error_code": "FORBIDDEN", "message": "You cannot view this session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not session.end_time and not session.is_time_up():
            return Response(
                {"error_code": "SESSION_ACTIVE", "message": "Session is still active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_set = get_valid_words(session.challenge)
        all_valid = sorted(valid_set)
        found = sorted(
            {s.get("word") for s in session.submissions if s.get("is_valid")}
        )
        payload = {
            "all_valid_words": all_valid,
            "found_words": found,
            "score": session.score,
        }
        return Response(payload, status=status.HTTP_200_OK)

    def _is_owner_or_guest(self, session, request):
        if session.player_user_id is None:
            return True
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk) == session.player_user_id
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id) == session.player_user_id
        return False


class SessionHintView(APIView):
    """
    Provide a simple hint for active sessions (FR-08).
    """

    def get(self, request, pk):
        session = get_object_or_404(GameSession.objects.select_related('challenge'), pk=pk)

        if not self._is_owner_or_guest(session, request):
            return Response(
                {"error_code": "FORBIDDEN", "message": "You cannot view this session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.is_time_up():
            return Response(
                {"error_code": "TIME_UP", "message": "Session has ended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.hint_uses >= 3:
            return Response(
                {"error_code": "HINT_LIMIT_REACHED", "message": "Hint limit reached for this session."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        valid_set = get_valid_words(session.challenge)
        found_set = {s.get("word") for s in session.submissions if s.get("is_valid")}
        unfound = sorted(valid_set - found_set)
        hint = choose_hint(unfound)
        session.hint_uses += 1
        session.save(update_fields=['hint_uses'])
        return Response({"hint": hint, "remaining": max(0, 3 - session.hint_uses)}, status=status.HTTP_200_OK)

    def _is_owner_or_guest(self, session, request):
        if session.player_user_id is None:
            return True
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk) == session.player_user_id
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id) == session.player_user_id
        return False


class SessionEndView(APIView):
    """
    Explicitly end a session (FR-06).
    """

    def post(self, request, pk):
        session = get_object_or_404(GameSession.objects.select_related('challenge'), pk=pk)

        if not self._is_owner_or_guest(session, request):
            return Response(
                {"error_code": "FORBIDDEN", "message": "You cannot end this session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not session.end_time:
            session.end_time = timezone.now()
            session.save(update_fields=['end_time'])

        # Cleanup guest practice sessions/challenges after end
        if session.mode == GameSession.MODE_PRACTICE and session.player_user_id is None:
            challenge = session.challenge
            session.delete()
            # If no other sessions refer to this practice challenge, delete it too
            if not GameSession.objects.filter(challenge=challenge).exists():
                challenge.delete()
            return Response({"status": "ended_and_deleted", "session_id": pk}, status=status.HTTP_200_OK)

        return Response({"status": "ended", "session_id": session.id}, status=status.HTTP_200_OK)

    def _is_owner_or_guest(self, session, request):
        if session.player_user_id is None:
            return True
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk) == session.player_user_id
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id) == session.player_user_id
        return False
