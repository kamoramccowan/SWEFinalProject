from django.contrib.auth.models import AbstractUser
from django.db import models


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
