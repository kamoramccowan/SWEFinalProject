from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserSettings

User = get_user_model()


class AuthenticatedUserSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "firebase_uid", "email", "display_name", "is_registered", "role")
        read_only_fields = fields

    def get_is_registered(self, obj) -> bool:
        return bool(obj and obj.is_authenticated)

    def get_role(self, obj) -> str:
        return "registered" if obj and obj.is_authenticated else "guest"


class UserSettingsSerializer(serializers.ModelSerializer):
    allowed_sender_user_ids = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = UserSettings
        fields = ["challenge_visibility", "allow_incoming_challenges", "allowed_sender_user_ids"]
        read_only_fields = []
