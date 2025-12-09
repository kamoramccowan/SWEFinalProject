from django.db import models
from django.utils import timezone

# Dev A scan (FR-05): No session model exists yet; adding GameSession tied to Challenge.
# Prior work: FR-02 Challenge model, FR-03 recipients/status, FR-04 soft-delete with active manager.


class ChallengeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Challenge.STATUS_ACTIVE)


class ChallengeManager(models.Manager):
    def get_queryset(self):
        return ChallengeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class Challenge(models.Model):
    DIFFICULTY_EASY = "easy"
    DIFFICULTY_MEDIUM = "medium"
    DIFFICULTY_HARD = "hard"
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, "Easy"),
        (DIFFICULTY_MEDIUM, "Medium"),
        (DIFFICULTY_HARD, "Hard"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_DELETED = "deleted"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_DELETED, "Deleted"),
    ]

    creator_user_id = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    grid = models.JSONField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    valid_words = models.JSONField(default=list, blank=True)
    recipients = models.JSONField(default=list, blank=True)  # list of intended recipient identifiers
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ChallengeManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Challenge {self.id} ({self.difficulty})'


class GameSession(models.Model):
    MODE_CHALLENGE = "challenge"
    MODE_PRACTICE = "practice"
    MODE_CHOICES = [
        (MODE_CHALLENGE, "Challenge"),
        (MODE_PRACTICE, "Practice"),
    ]

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='sessions')
    player_user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_CHALLENGE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)  # will be set by FR-13
    score = models.IntegerField(default=0)
    submissions = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['challenge']),
            models.Index(fields=['player_user_id']),
        ]

    def __str__(self):
        return f'Session {self.id} on challenge {self.challenge_id}'

    def is_time_up(self, now=None):
        """
        Check if the session is over due to time expiry or explicit end.
        """
        if self.end_time:
            return True
        if self.duration_seconds is None:
            return False
        current_time = now or timezone.now()
        return current_time >= self.start_time + timezone.timedelta(seconds=self.duration_seconds)
