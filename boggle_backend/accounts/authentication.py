import re
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.crypto import get_random_string
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .firebase_auth import FirebaseVerificationError, verify_firebase_id_token

User = get_user_model()


class FirebaseAuthentication(BaseAuthentication):
    """
    DRF authentication backend that validates Firebase ID tokens and maps them to Users.
    """

    keyword = "bearer"

    def authenticate(self, request) -> Optional[Tuple[User, dict]]:
        id_token = self._get_token_from_header(request)
        claims = self._verify_token(id_token)

        uid = claims.get("uid")
        if not uid:
            raise AuthenticationFailed(
                {"error_code": "INVALID_TOKEN", "message": "Firebase token is missing uid claim."}
            )

        user = self._get_or_create_user(uid, claims)
        return user, claims

    def authenticate_header(self, request) -> str:
        return "Bearer"

    def _get_token_from_header(self, request) -> str:
        auth_header = get_authorization_header(request).decode("utf-8")
        if not auth_header:
            raise AuthenticationFailed(
                {"error_code": "AUTH_HEADER_MISSING", "message": "Authorization header is missing."}
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword:
            raise AuthenticationFailed(
                {
                    "error_code": "INVALID_AUTH_HEADER",
                    "message": "Authorization header must be in the format: Bearer <token>.",
                }
            )

        return parts[1]

    def _verify_token(self, id_token: str) -> dict:
        try:
            return verify_firebase_id_token(id_token)
        except FirebaseVerificationError as exc:
            raise AuthenticationFailed({"error_code": exc.code, "message": exc.message})

    def _get_or_create_user(self, uid: str, claims: dict) -> User:
        display_name = claims.get("name") or claims.get("display_name") or ""
        email = claims.get("email") or ""

        defaults = {
            "username": self._build_username(uid),
            "firebase_uid": uid,
            "display_name": display_name,
            "email": email,
        }

        try:
            user, created = User.objects.get_or_create(firebase_uid=uid, defaults=defaults)
        except IntegrityError:
            # Handle rare username collision by retrying with a randomized username.
            defaults["username"] = self._build_username(uid, add_random_suffix=True)
            user, created = User.objects.get_or_create(firebase_uid=uid, defaults=defaults)

        if not created:
            updated_fields = []
            if email and user.email != email:
                user.email = email
                updated_fields.append("email")
            if display_name and user.display_name != display_name:
                user.display_name = display_name
                updated_fields.append("display_name")
            if updated_fields:
                updated_fields.append("updated_at")
                user.save(update_fields=updated_fields)

        return user

    def _build_username(self, uid: str, add_random_suffix: bool = False) -> str:
        safe_uid = re.sub(r"[^a-zA-Z0-9._-]", "_", uid)
        suffix = f"_{get_random_string(6).lower()}" if add_random_suffix else ""
        candidate = f"fb_{safe_uid}{suffix}"
        return candidate[:150]
