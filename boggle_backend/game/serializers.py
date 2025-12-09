from rest_framework import serializers

from .models import Challenge, GameSession
from .difficulty import get_difficulty_config, validate_grid_for_difficulty

# Dev A scan (FR-02): We added a Challenge serializer here because no serializer existed in this app; a legacy serializer lives in the "api" app.
# Plan for FR-03: Reuse Challenge model and add a slim list serializer for "my challenges" to avoid sending heavy fields; include recipients/status fields to match FR-03.
# Plan for FR-05: Add GameSession serializer for starting challenge sessions, validating active challenge and binding player_user_id from request.
# Plan for FR-06: Add a submission serializer for one-word submission.


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = [
            'id',
            'creator_user_id',
            'title',
            'description',
            'grid',
            'difficulty',
            'valid_words',
            'recipients',
            'status',
            'share_slug',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'creator_user_id', 'valid_words', 'status', 'share_slug', 'created_at', 'updated_at')

    def validate_recipients(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Recipients must be a list of identifiers (e.g., emails/usernames).")
        cleaned = []
        for item in value:
            text = str(item).strip()
            if text:
                cleaned.append(text)
        return cleaned

    def validate_grid(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Grid must be a non-empty square matrix.")

        if not all(isinstance(row, list) for row in value):
            raise serializers.ValidationError("Each grid row must be a list.")

        row_lengths = {len(row) for row in value}
        if len(row_lengths) != 1:
            raise serializers.ValidationError("Grid must be square (all rows same length).")

        size = row_lengths.pop()
        if size == 0:
            raise serializers.ValidationError("Grid rows cannot be empty.")

        normalized = []
        for row in value:
            normalized_row = []
            for cell in row:
                cell_str = "" if cell is None else str(cell).strip()
                if not cell_str:
                    raise serializers.ValidationError("Grid cells cannot be empty.")
                if not cell_str.isalpha():
                    raise serializers.ValidationError("Grid cells must contain letters only.")
                normalized_row.append(cell_str.upper())
            normalized.append(normalized_row)

        return normalized

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user_id = self._get_request_user_id()
        if not user_id:
            raise serializers.ValidationError({"creator_user_id": ["Authenticated user is required."]})
        attrs['creator_user_id'] = user_id
        difficulty = attrs.get('difficulty')
        grid = attrs.get('grid') or []
        if difficulty and grid:
            cfg = get_difficulty_config(difficulty)
            if cfg and not validate_grid_for_difficulty(grid, difficulty):
                raise serializers.ValidationError({"grid": [f"Grid must be {cfg['grid_size']}x{cfg['grid_size']} for {difficulty}."]})
        return attrs

    def _get_request_user_id(self):
        """
        Pull a trusted user identifier from the request context; never accept it from the payload.
        """
        request = self.context.get('request')
        if not request:
            return None

        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)

        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)

        return None


class ChallengeListSerializer(serializers.ModelSerializer):
    """Slim serializer for listing current user's challenges without heavy fields."""

    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'description',
            'difficulty',
            'recipients',
            'status',
            'created_at',
        ]


class GameSessionSerializer(serializers.ModelSerializer):
    challenge_id = serializers.IntegerField(write_only=True)
    challenge = serializers.PrimaryKeyRelatedField(read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True, allow_null=True)
    submissions = serializers.JSONField(read_only=True)

    class Meta:
        model = GameSession
        fields = [
            'id',
            'challenge',
            'challenge_id',
            'player_user_id',
            'mode',
            'start_time',
            'end_time',
            'duration_seconds',
            'score',
            'submissions',
        ]
        read_only_fields = (
            'id',
            'challenge',
            'player_user_id',
            'start_time',
            'end_time',
            'duration_seconds',
            'score',
            'submissions',
        )

    def validate_challenge_id(self, value):
        try:
            return Challenge.objects.active().get(pk=value)
        except Challenge.DoesNotExist:
            raise serializers.ValidationError("Challenge not found or unavailable.")

    def validate_mode(self, value):
        if value not in dict(GameSession.MODE_CHOICES):
            raise serializers.ValidationError("Invalid mode.")
        return value

    def create(self, validated_data):
        challenge = validated_data.pop('challenge_id')
        user_id = self._get_request_user_id()
        return GameSession.objects.create(
            challenge=challenge,
            player_user_id=user_id,
            mode=validated_data.get('mode', GameSession.MODE_CHALLENGE),
        )

    def _get_request_user_id(self):
        request = self.context.get('request')
        if not request:
            return None
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None


class SessionResultsSerializer(serializers.Serializer):
    all_valid_words = serializers.ListField(child=serializers.CharField())
    found_words = serializers.ListField(child=serializers.CharField())
    score = serializers.IntegerField()


class SessionSubmitWordSerializer(serializers.Serializer):
    word = serializers.CharField(max_length=64)

    def validate_word(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Word cannot be empty.")
        return value
