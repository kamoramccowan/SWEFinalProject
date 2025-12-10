from datetime import timedelta
from typing import Dict

from django.db.models import Avg, Count, Max
from django.db.models.functions import TruncDate

from game.models import GameSession


def compute_user_stats(user_id: str | int) -> Dict:
    """
    Aggregate basic stats for the given user across finished sessions.
    """
    user_id_str = str(user_id)
    sessions = GameSession.objects.filter(player_user_id=user_id_str, end_time__isnull=False)

    aggregates = sessions.aggregate(
        games_played=Count("id"),
        average_score=Avg("score"),
        best_score=Max("score"),
    )

    days = list(
        sessions.annotate(day=TruncDate("end_time"))
        .values_list("day", flat=True)
        .distinct()
    )
    current_streak, longest_streak = _compute_streaks(days)

    total_valid_words = 0
    total_submissions = 0
    for submission_list in sessions.values_list("submissions", flat=True):
        if isinstance(submission_list, list):
            total_submissions += len(submission_list)
            total_valid_words += sum(
                1 for item in submission_list if isinstance(item, dict) and item.get("is_valid")
            )

    incorrect_submissions = max(0, total_submissions - total_valid_words)
    accuracy = round(total_valid_words / total_submissions, 3) if total_submissions else 0

    return {
        "games_played": aggregates.get("games_played") or 0,
        "average_score": aggregates.get("average_score") or 0,
        "best_score": aggregates.get("best_score") or 0,
        "total_valid_words_found": total_valid_words,
        "total_submissions": total_submissions,
        "correct_submissions": total_valid_words,
        "incorrect_submissions": incorrect_submissions,
        "accuracy": accuracy,
        "days_played": len(days),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


def _compute_streaks(days) -> tuple[int, int]:
    """
    Given a list of dates, compute current and longest streak of consecutive days.
    """
    if not days:
        return 0, 0

    sorted_days = sorted(set(days))
    longest = 1
    run = 1
    for i in range(1, len(sorted_days)):
        if sorted_days[i] == sorted_days[i - 1] + timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    # current streak: walk backward from most recent date
    current = 1
    cursor = sorted_days[-1]
    for i in range(len(sorted_days) - 2, -1, -1):
        if sorted_days[i] == cursor - timedelta(days=1):
            current += 1
            cursor = sorted_days[i]
        else:
            break

    return current, longest
