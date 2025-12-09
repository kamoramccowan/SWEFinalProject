from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404

from .models import Challenge
from .serializers import ChallengeSerializer, ChallengeListSerializer

# Dev A scan (FR-02): No game endpoints existed; legacy challenge endpoints are in api/views.py.
# Plan for FR-03: Add a "my challenges" listing that filters by authenticated user and reuses the Challenge model with a slim serializer.
# Plan for FR-04: Add delete (soft-delete) endpoint; ensure only creators can delete and deleted challenges are excluded from listings.


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


class ChallengeMineView(ListAPIView):
    """
    List challenges created by the authenticated user (FR-03).
    """

    serializer_class = ChallengeListSerializer

    def get_queryset(self):
        user_id = self._get_user_id()
        if not user_id:
            return Challenge.objects.none()
        return Challenge.objects.filter(
            creator_user_id=str(user_id),
            status=Challenge.STATUS_ACTIVE,
        ).order_by('-created_at')

    def _get_user_id(self):
        request = self.request
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None


class ChallengeDeleteView(APIView):
    """
    Soft-delete a challenge owned by the authenticated user (FR-04).
    """

    def delete(self, request, pk):
        challenge = get_object_or_404(Challenge.objects.active(), pk=pk)
        user_id = self._get_user_id(request)
        if not user_id or challenge.creator_user_id != str(user_id):
            return Response(
                {
                    "error_code": "FORBIDDEN",
                    "message": "You are not allowed to delete this challenge.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        challenge.status = Challenge.STATUS_DELETED
        challenge.save(update_fields=['status', 'updated_at'])
        return Response({"status": "deleted"}, status=status.HTTP_200_OK)

    def _get_user_id(self, request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return str(user.pk)
        if hasattr(request, 'user_id'):
            user_id = getattr(request, 'user_id')
            if user_id is not None:
                return str(user_id)
        return None
