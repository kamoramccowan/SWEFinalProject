from datetime import date
from typing import List, Dict, Any, Tuple

from django.contrib.auth import get_user_model
from django.db.models import F

from accounts.daily import get_or_create_daily_challenge
from game.models import GameSession

User = get_user_model()


def _session_queryset_for_challenge(challenge_id: int):
    return GameSession.objects.filter(
        challenge_id=challenge_id,
        end_time__isnull=False,
        mode=GameSession.MODE_CHALLENGE,
    )


def get_challenge_leaderboard(challenge_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get leaderboard aggregated by user - one entry per user with their stats.
    """
    from django.db.models import Max, Count, Sum
    
    # Aggregate sessions by player_user_id
    qs = (
        _session_queryset_for_challenge(challenge_id)
        .values("player_user_id")
        .annotate(
            total_score=Sum("score"),
            games_played=Count("id"),
            best_score=Max("score"),
        )
        .order_by("-total_score", "-best_score")
    )[:limit]
    
    entries = []
    for row in qs:
        entries.append({
            "player_user_id": row["player_user_id"],
            "score": row["best_score"],
            "total_score": row["total_score"],
            "games_played": row["games_played"],
            "wins": 0,  # Will calculate below
        })
    
    # Calculate wins (entries where this user had the highest score for the challenge)
    # For simplicity, mark top scorer(s) as having 1 win per leaderboard
    if entries:
        top_score = entries[0]["total_score"]
        for e in entries:
            if e["total_score"] == top_score:
                e["wins"] = 1
    
    _attach_user_display_names(entries)
    _assign_ranks(entries)
    return entries


def get_daily_leaderboard(for_date: date, limit: int = 50) -> Tuple[int, List[Dict[str, Any]]]:
    daily = get_or_create_daily_challenge(for_date)
    entries = get_challenge_leaderboard(daily.challenge_id, limit=limit)
    return daily.challenge_id, entries


def compute_session_rank(session: GameSession) -> Dict[str, int]:
    qs = _session_queryset_for_challenge(session.challenge_id)
    total_players = qs.count()

    higher = qs.filter(
        score__gt=session.score
    ).count()

    tie_better_time = qs.filter(
        score=session.score,
        end_time__lt=session.end_time
    ).count()

    rank = higher + tie_better_time + 1
    return {"rank": rank, "total_players": total_players}


def milestone_for_rank(rank: int) -> str | None:
    if rank is None:
        return None
    if rank == 1:
        return "top1"
    if rank <= 5:
        return "top5"
    if rank <= 10:
        return "top10"
    return None


def _attach_user_display_names(entries: List[Dict[str, Any]]):
    user_ids = [e["player_user_id"] for e in entries if e.get("player_user_id")]
    id_map = {}
    if user_ids:
        users = User.objects.filter(id__in=user_ids).values("id", "display_name")
        id_map = {str(u["id"]): u["display_name"] or "" for u in users}
    for e in entries:
        uid = e.get("player_user_id")
        e["display_name"] = id_map.get(str(uid), "") if uid else ""


def _assign_ranks(entries: List[Dict[str, Any]]):
    """Assign ranks based on total_score (ties get same rank)."""
    last_score = None
    current_rank = 0
    for idx, e in enumerate(entries):
        score = e.get("total_score") or e.get("score") or 0
        if score != last_score:
            current_rank = idx + 1
            last_score = score
        e["rank"] = current_rank
