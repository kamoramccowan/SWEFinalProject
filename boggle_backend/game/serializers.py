from rest_framework import serializers

from .models import Challenge, GameSession
from .difficulty import get_difficulty_config, validate_grid_for_difficulty
from .word_solver import solve_boggle
from django.utils import timezone
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
            'duration_seconds',
            'difficulty',
            'language',
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
        if size not in {4, 5, 6}:
            raise serializers.ValidationError("Grid size must be 4x4, 5x5, or 6x6.")

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
        duration_seconds = attrs.get('duration_seconds')
        if difficulty and grid:
            cfg = get_difficulty_config(difficulty)
            if cfg and not validate_grid_for_difficulty(grid, difficulty):
                raise serializers.ValidationError({"grid": [f"Grid must be {cfg['grid_size']}x{cfg['grid_size']} for {difficulty}."]})
            if duration_seconds is None:
                attrs['duration_seconds'] = cfg["duration_seconds"]
        if duration_seconds is not None:
            try:
                val = int(duration_seconds)
            except (TypeError, ValueError):
                raise serializers.ValidationError({"duration_seconds": ["Must be an integer (seconds)."]})
            if val < 30 or val > 900:
                raise serializers.ValidationError({"duration_seconds": ["Must be between 30 and 900 seconds."]})
            attrs['duration_seconds'] = val
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

    def create(self, validated_data):
        """Create challenge and populate valid_words using the boggle solver."""
        grid = validated_data.get('grid', [])
        # Get language from validated_data (keep it for model save)
        language = validated_data.get('language', 'en')
        
        # Solve the boggle to find all valid words
        try:
            valid_words = solve_boggle(grid, language=language)
        except Exception as e:
            # If solver fails, use empty list as fallback
            valid_words = []
        
        validated_data['valid_words'] = valid_words
        
        return super().create(validated_data)


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
    remaining_seconds = serializers.SerializerMethodField()
    challenge_title = serializers.SerializerMethodField()
    challenge_grid = serializers.SerializerMethodField()
    challenge_difficulty = serializers.SerializerMethodField()
    players = serializers.SerializerMethodField()

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
            'remaining_seconds',
            'challenge_title',
            'challenge_grid',
            'challenge_difficulty',
            'players',
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
            'remaining_seconds',
            'challenge_title',
            'challenge_grid',
            'challenge_difficulty',
            'players',
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
        from .difficulty import get_difficulty_config
        cfg = get_difficulty_config(challenge.difficulty)
        duration = challenge.duration_seconds or (cfg["duration_seconds"] if cfg else None)
        return GameSession.objects.create(
            challenge=challenge,
            player_user_id=user_id,
            mode=validated_data.get('mode', GameSession.MODE_CHALLENGE),
            duration_seconds=duration,
        )

    def get_challenge_title(self, obj):
        if obj.challenge_id and obj.challenge:
            return obj.challenge.title
        return None

    def get_challenge_grid(self, obj):
        if obj.challenge_id and obj.challenge:
            return obj.challenge.grid
        return None

    def get_challenge_difficulty(self, obj):
        if obj.challenge_id and obj.challenge:
            return obj.challenge.difficulty
        return None

    def get_remaining_seconds(self, obj):
        if obj.duration_seconds is None or obj.start_time is None:
            return None
        now = timezone.now()
        elapsed = max(0, int((now - obj.start_time).total_seconds()))
        return max(0, obj.duration_seconds - elapsed)

    def get_players(self, obj):
        """
        Return simple player list for the same challenge: name/email fallback, score, words, status, leader flag.
        """
        from accounts.models import User

        sessions = GameSession.objects.filter(challenge=obj.challenge).only(
            "id", "player_user_id", "score", "end_time", "submissions", "start_time"
        )
        user_ids = {s.player_user_id for s in sessions if s.player_user_id}

        numeric_ids = [uid for uid in user_ids if uid and str(uid).isdigit()]
        firebase_ids = [uid for uid in user_ids if uid and not str(uid).isdigit()]

        users_by_pk = {str(u.id): u for u in User.objects.filter(id__in=numeric_ids)} if numeric_ids else {}
        users_by_fb = {u.firebase_uid: u for u in User.objects.filter(firebase_uid__in=firebase_ids)} if firebase_ids else {}

        players_map = {}
        for s in sessions:
            uid = s.player_user_id or "guest"
            uid_str = str(uid)
            user_obj = users_by_pk.get(uid_str) or users_by_fb.get(uid_str)
            name = self._display_name(user_obj, uid_str)
            words = sum(1 for sub in s.submissions if sub.get("is_valid"))
            status = "Finished" if s.end_time else "Playing"

            existing = players_map.get(uid_str)
            if not existing or (existing.get("score", 0) < (s.score or 0)):
                players_map[uid_str] = {
                    "name": name,
                    "score": s.score or 0,
                    "words": words,
                    "status": status,
                    "leader": False,
                }

        players = list(players_map.values())
        if players:
            top_score = max(p["score"] for p in players)
            for p in players:
                p["leader"] = p["score"] == top_score
        return players

    def _display_name(self, user_obj, uid_str):
        if user_obj:
            return user_obj.display_name or user_obj.email or user_obj.username or "Player"
        if uid_str.startswith("stub_"):
            return "Player"
        if uid_str.startswith("fb_stub_"):
            return "Player"
        if len(uid_str) > 24:
            return f"{uid_str[:12]}…{uid_str[-6:]}"
        return uid_str or "Player"

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
