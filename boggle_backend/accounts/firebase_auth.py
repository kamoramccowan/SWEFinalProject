import os


class FirebaseVerificationError(Exception):
    """
    Lightweight error wrapper so we can return structured DRF responses without leaking tokens.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return its decoded claims.

    Production path uses the Firebase Admin SDK. For local development without Firebase,
    set FIREBASE_AUTH_STUB_MODE=1 (default) to accept the raw token string as a uid.
    """
    if not id_token:
        raise FirebaseVerificationError("MISSING_ID_TOKEN", "Authentication token is required.")

    # Default to stub mode unless explicitly disabled (FIREBASE_AUTH_STUB_MODE=0).
    stub_mode = os.environ.get("FIREBASE_AUTH_STUB_MODE", "1") != "0"
    if stub_mode:
        # Dev-only path: derive a safe uid from the token (hash + short prefix) to respect DB length limits.
        token_str = str(id_token)
        if len(token_str) > 120:
            import hashlib
            token_hash = hashlib.sha256(token_str.encode("utf-8")).hexdigest()
            uid = f"stub_{token_hash[:32]}"
        else:
            uid = token_str
        return {"uid": uid, "email": None, "name": None, "firebase_sign_in_provider": "stub"}

    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth
    except ImportError as exc:
        raise FirebaseVerificationError(
            "FIREBASE_ADMIN_NOT_CONFIGURED",
            "Firebase Admin SDK is not installed or configured. Set FIREBASE_AUTH_STUB_MODE=1 for local dev or add credentials.",
        ) from exc

    if not firebase_admin._apps:
        try:
            firebase_admin.initialize_app()
        except Exception as exc:  # pragma: no cover - depends on env configuration
            raise FirebaseVerificationError(
                "FIREBASE_ADMIN_INIT_FAILED",
                "Firebase Admin SDK could not initialize. Check GOOGLE_APPLICATION_CREDENTIALS or service account config.",
            ) from exc

    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as exc:
        raise FirebaseVerificationError("INVALID_ID_TOKEN", "The authentication token is invalid or expired.") from exc
