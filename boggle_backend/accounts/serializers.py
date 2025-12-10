from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserSettings

User = get_user_model()


class AuthenticatedUserSerializer(serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "firebase_uid", "email", "display_name", "avatar_url", "is_registered", "role")
        read_only_fields = fields

    def get_is_registered(self, obj) -> bool:
        return bool(obj and obj.is_authenticated)

    def get_role(self, obj) -> str:
        return "registered" if obj and obj.is_authenticated else "guest"


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile fields (display_name, avatar_url)."""

    class Meta:
        model = User
        fields = ["display_name", "avatar_url"]

    def validate_avatar_url(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("Avatar URL is too long (max 500 characters).")
        return value


class UserSettingsSerializer(serializers.ModelSerializer):
    allowed_sender_user_ids = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = UserSettings
        fields = ["challenge_visibility", "allow_incoming_challenges", "allowed_sender_user_ids", "theme"]
        read_only_fields = []

    def validate_theme(self, value):
        allowed = {choice[0] for choice in UserSettings.THEME_CHOICES}
        if value not in allowed:
            raise serializers.ValidationError(f"Theme must be one of: {', '.join(sorted(allowed))}.")
        return value

