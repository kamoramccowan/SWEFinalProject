"""
Lightweight mail helper for challenge sharing.

In production, wire this to a real email backend (e.g., SendGrid/SES).
For now, we stub to allow integration without outbound SMTP configured.
"""


def send_challenge_email(recipient_email: str, share_link: str, sender_name: str = "", challenge_title: str = "") -> bool:
    """
    Send (or stub) a challenge invite email. Returns True if "sent".
    """
    if not recipient_email or not share_link:
        return False
    # TODO: integrate real email backend. For now, stub succeeds.
    return True
