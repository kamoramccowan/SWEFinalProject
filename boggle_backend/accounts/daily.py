import random
from datetime import date
from typing import Optional

from django.utils import timezone

from game.models import Challenge
from game.word_solver import generate_solvable_grid, solve_boggle
from .models import DailyChallenge, DailyChallengeResult, User


def get_or_create_daily_challenge(for_date: date) -> DailyChallenge:
    """
    Lazy resolver for the daily challenge:
    - If already set for the date, return it.
    - Otherwise, pick or generate a challenge and record it.
    """
    daily = DailyChallenge.objects.filter(date=for_date).select_related("challenge").first()
    if daily:
        return daily

    challenge = pick_or_generate_challenge()
    daily = DailyChallenge.objects.create(date=for_date, challenge=challenge, source="generated")
    return daily


def pick_or_generate_challenge() -> Challenge:
    """
    Choose a random active challenge with valid words.
    If none exist or none have valid words, generate a new solvable challenge.
    """
    # First, try to find an existing challenge with valid_words
    active = list(Challenge.objects.active().exclude(valid_words=[]))
    if active:
        return random.choice(active)
    
    # No valid challenges exist - generate a new one
    return generate_daily_challenge()


def generate_daily_challenge() -> Challenge:
    """
    Generate a new solvable challenge for the daily.
    """
    # Generate a solvable 4x4 grid with medium difficulty
    grid, valid_words = generate_solvable_grid(size=4, difficulty='medium', language='en', min_words=20)
    
    # Create the challenge with the generated grid
    challenge = Challenge.objects.create(
        title=f"Daily Challenge {date.today().strftime('%Y-%m-%d')}",
        description="Auto-generated daily challenge",
        grid=grid,
        valid_words=valid_words,
        duration_seconds=180,  # 3 minutes
        difficulty='medium',
        language='en',
        status='active',
    )
    return challenge


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
