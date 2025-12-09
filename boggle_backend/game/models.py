from django.db import models

# Dev A scan: The legacy "api" app already contains a Challenge model/endpoints.
# For FR-02 we add a dedicated game app model to own challenge creation with the required fields.


class Challenge(models.Model):
    DIFFICULTY_EASY = "easy"
    DIFFICULTY_MEDIUM = "medium"
    DIFFICULTY_HARD = "hard"
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, "Easy"),
        (DIFFICULTY_MEDIUM, "Medium"),
        (DIFFICULTY_HARD, "Hard"),
    ]

    creator_user_id = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    grid = models.JSONField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    valid_words = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Challenge {self.id} ({self.difficulty})'
