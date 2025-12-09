from rest_framework import serializers

from .models import Challenge, Games
from .services import DictionaryNotFound, generate_valid_words, normalize_grid

# creating a model class below
class GamesSerializer(serializers.ModelSerializer):
    class Meta:
            model = Games
            fields = '__all__'


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'creator',
            'difficulty',
            'grid_size',
            'grid',
            'clues',
            'description',
            'valid_words',
            'created_at',
        ]
        read_only_fields = ('valid_words', 'created_at')

    def validate_creator(self, value):
        creator = str(value).strip()
        if not creator:
            raise serializers.ValidationError("Creator is required.")
        return creator

    def validate_clues(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Clues must be provided as a list.")
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned

    def validate_grid(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Grid must be a non-empty list of rows.")
        if not all(isinstance(row, list) for row in value):
            raise serializers.ValidationError("Each grid row must be a list.")

        normalized = normalize_grid(value)
        row_lengths = {len(row) for row in normalized}
        if len(row_lengths) != 1:
            raise serializers.ValidationError("All grid rows must have the same number of cells.")
        if any(cell == "" for row in normalized for cell in row):
            raise serializers.ValidationError("Grid cells cannot be empty.")
        return normalized

    def validate(self, attrs):
        grid = attrs.get('grid') or []
        grid_size = attrs.get('grid_size') or (len(grid) if isinstance(grid, list) else None)
        if grid_size is None:
            raise serializers.ValidationError({"grid_size": "Grid size is required."})

        allowed_sizes = {4, 5, 6}
        if grid_size not in allowed_sizes:
            raise serializers.ValidationError({"grid_size": "Grid size must be 4, 5, or 6."})

        if any(len(row) != grid_size for row in grid):
            raise serializers.ValidationError({"grid": f"Grid must be {grid_size}x{grid_size}."})

        attrs['grid_size'] = grid_size
        return attrs

    def create(self, validated_data):
        grid = validated_data['grid']
        try:
            validated_data['valid_words'] = generate_valid_words(grid)
        except DictionaryNotFound as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc
        return super().create(validated_data)
