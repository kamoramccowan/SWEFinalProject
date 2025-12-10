import random
from datetime import date
from typing import Optional

from django.utils import timezone

from game.models import Challenge
from .models import DailyChallenge, DailyChallengeResult, User


def get_or_create_daily_challenge(for_date: date) -> DailyChallenge:
    """
    Lazy resolver for the daily challenge:
    - If already set for the date, return it.
    - Otherwise, pick a random active challenge and record it.
    """
    daily = DailyChallenge.objects.filter(date=for_date).select_related("challenge").first()
    if daily:
        return daily

    challenge = pick_active_challenge()
    daily = DailyChallenge.objects.create(date=for_date, challenge=challenge, source="random")
    return daily


def pick_active_challenge() -> Challenge:
    """
    Choose a random active challenge. If none exist, raise a clear error.
    """
    active = list(Challenge.objects.active())
    if not active:
        raise ValueError("No active challenges available to serve as daily challenge.")
    return random.choice(active)


def record_daily_result(challenge: Challenge, user, session_score: int, session_obj=None, player_user_id: str | None = None):
    """
    Upsert the user's score for today's daily challenge if the challenge matches today's daily.
    """
    today = date.today()
    daily = DailyChallenge.objects.filter(date=today, challenge=challenge).first()
    if not daily:
        return

    # Resolve the user either from the authenticated request or from the stored player_user_id.
    resolved_user = None
    if user and getattr(user, "is_authenticated", False):
        resolved_user = user
    elif player_user_id:
        try:
            resolved_user = User.objects.get(pk=player_user_id)
        except User.DoesNotExist:
            # Try integer coercion as a fallback
            try:
                resolved_user = User.objects.get(pk=int(player_user_id))
            except Exception:
                resolved_user = None
    if not resolved_user:
        return

    result, created = DailyChallengeResult.objects.get_or_create(
        daily_challenge=daily,
        user=resolved_user,
        defaults={"score": session_score, "session": session_obj},
    )
    if not created and session_score > result.score:
        result.score = session_score
        if session_obj:
            result.session = session_obj
        result.save(update_fields=["score", "session", "updated_at"])
