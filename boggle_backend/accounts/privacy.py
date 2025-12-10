from accounts.models import UserSettings


def can_receive_challenge(user, sender=None) -> bool:
    """
    Return True if the given user allows incoming targeted challenges.
    Share-links are out of scope for this helper (treated as public).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    settings, _ = UserSettings.objects.get_or_create(user=user)
    if not settings.allow_incoming_challenges or settings.challenge_visibility == UserSettings.VISIBILITY_NO_ONE:
        return False
    allowed_list = settings.allowed_sender_user_ids or []
    if allowed_list:
        sender_id = str(getattr(sender, "id", "") or "")
        return sender_id and sender_id in {str(x) for x in allowed_list}
    return True
