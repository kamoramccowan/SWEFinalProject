from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ChallengeSerializer

# Dev A scan: No game endpoints existed; legacy challenge endpoints are in api/views.py.
# For FR-02 we add a POST /api/challenges/ endpoint here that binds creator_user_id from the request.


class ChallengeCreateView(APIView):
    """
    Create a new challenge using the authenticated user's id as creator_user_id.
    """

    def post(self, request):
        serializer = ChallengeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            challenge = serializer.save()
            return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)

        return Response(
            {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid challenge payload.",
                "details": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
