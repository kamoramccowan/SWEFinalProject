from django.db import models

# creating a model class below
class Games(models.Model):
    name = models.CharField(max_length=50)
    size = models.IntegerField()
    grid = models.TextField() # Serialize the 2d array to a string:
    foundwords = models.TextField() #Serialize the array of words to a single string:

    def __str__(self):
        return f'Name: {self.name} Size: {self.size} Grid: {self.grid}'


class Challenge(models.Model):
    DIFFICULTY_EASY = "easy"
    DIFFICULTY_MEDIUM = "medium"
    DIFFICULTY_HARD = "hard"
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, "Easy"),
        (DIFFICULTY_MEDIUM, "Medium"),
        (DIFFICULTY_HARD, "Hard"),
    ]

    title = models.CharField(max_length=120, blank=True)
    creator = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    grid_size = models.PositiveSmallIntegerField()
    grid = models.JSONField()
    clues = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    valid_words = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Challenge {self.id} ({self.difficulty}) by {self.creator}'
