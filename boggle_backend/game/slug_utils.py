import secrets


def generate_share_slug() -> str:
    """Generate a URL-safe slug for sharing challenges."""
    return secrets.token_urlsafe(8)
