from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user that maps Firebase users to internal records while retaining Django's auth features.
    """

    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True, db_index=True)
    display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.display_name:
            return self.display_name
        if self.username:
            return self.username
        if self.email:
            return self.email
        return self.firebase_uid or super().__str__()


class DailyChallenge(models.Model):
    """
    Dev B (FR-14): Stores the global daily challenge per calendar date.
    """

    date = models.DateField(unique=True, db_index=True)
    challenge = models.ForeignKey("game.Challenge", on_delete=models.CASCADE, related_name="daily_entries")
    source = models.CharField(max_length=64, blank=True, default="random")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Daily {self.date} -> Challenge {self.challenge_id}"


class DailyChallengeResult(models.Model):
    """
    Dev B (FR-14 extension): Store per-user scores for the daily challenge.
    """

    daily_challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE, related_name="results")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="daily_results")
    session = models.ForeignKey("game.GameSession", null=True, blank=True, on_delete=models.SET_NULL)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("daily_challenge", "user")
        indexes = [
            models.Index(fields=["daily_challenge", "user"]),
        ]

    def __str__(self):
        return f"DailyResult {self.daily_challenge_id} user {self.user_id} score {self.score}"


# Dev B addition for FR-15: no schema change needed; ranking computed from GameSession.
