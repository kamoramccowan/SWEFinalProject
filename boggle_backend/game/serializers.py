from rest_framework import serializers

from .models import Challenge

# Dev A scan: No serializer in this app; legacy serializer lives in the "api" app.
# For FR-02 we add a Challenge serializer that validates the grid and binds creator_user_id from the request.


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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'creator_user_id', 'valid_words', 'created_at', 'updated_at')

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
