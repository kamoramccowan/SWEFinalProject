from rest_framework.permissions import BasePermission


class IsAuthenticatedFirebaseUser(BasePermission):
    message = {"error_code": "AUTH_REQUIRED", "message": "Authentication is required."}

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False))


class IsRegisteredUser(BasePermission):
    message = {"error_code": "AUTH_REQUIRED", "message": "Authentication is required for this action."}

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False))


class IsGuestOrRegistered(BasePermission):
    """
    Permits both guests and registered users; useful for endpoints that branch on user state.
    """

    def has_permission(self, request, view) -> bool:
        return True
