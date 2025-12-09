from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AuthenticatedUserSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "firebase_uid", "email", "display_name", "is_registered")
        read_only_fields = fields

    def get_is_registered(self, obj) -> bool:
        # FR-10 will refine guest vs registered; default to True for now.
        return True
