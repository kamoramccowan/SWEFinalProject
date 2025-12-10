from rest_framework.permissions import BasePermission


class IsAuthenticatedFirebaseUser(BasePermission):
    message = {"error_code": "AUTH_REQUIRED", "message": "Authentication is required."}

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False))
