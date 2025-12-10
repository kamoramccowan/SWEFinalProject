from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import FirebaseAuthentication
from .permissions import IsAuthenticatedFirebaseUser
from .serializers import AuthenticatedUserSerializer

# Dev B scan (FR-01): No existing auth endpoints or custom User model; project relies on Django's default user with no Firebase integration.
# Plan: add an accounts app with a custom User storing firebase_uid/display_name, a FirebaseAuthentication backend, a permission guard,
# and login verification / logout endpoints for Firebase-backed clients.


class LoginVerifyView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def post(self, request):
        serializer = AuthenticatedUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticatedFirebaseUser]

    def post(self, request):
        # Firebase logout is client-side; backend simply acknowledges and could clear server-side session if added.
        return Response(
            {
                "message": "Logout acknowledged. Firebase sessions are client-managed; no server token state to revoke.",
            },
            status=status.HTTP_200_OK,
        )
