from django.db import models

# Dev A scan: The legacy "api" app already contains a Challenge model/endpoints.
# For FR-02 we added a dedicated game app model. For FR-03 we added recipients/status.
# For FR-04 we introduce an active manager and rely on status for soft-delete behavior.


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
