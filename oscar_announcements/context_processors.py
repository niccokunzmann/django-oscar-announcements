def announcements(request):
    """Inject active announcements into the template context.

    Provides ``site_announcements`` — a list of
    :class:`~oscar_announcements.models.Announcement` instances the current
    user should see.  Includes ``visibility="creator"`` announcements for the
    user who created them (useful for previewing before going live).
    """
    from .models import Announcement

    if not request.user.is_authenticated:
        return {}

    excluded = set(request.session.get("excluded_announcements", []))
    return {
        "site_announcements": list(
            Announcement.active_for_user(request.user, excluded_pks=excluded)
        )
    }
