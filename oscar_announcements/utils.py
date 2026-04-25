from .models import Announcement

SESSION_KEY = "excluded_announcements"


def transfer_session_dismissals(user, session):
    """Promote session-dismissed announcements to permanent DB dismissals.

    Call this after a user logs in so that anything they dismissed anonymously
    is not shown to them again.  When Oscar is installed this is wired
    automatically to ``oscar.apps.customer.signals.user_logged_in`` in
    ``OscarAnnouncementsConfig.ready()``.
    """
    pks = session.get(SESSION_KEY, [])
    if not pks:
        return
    for ann in Announcement.objects.filter(pk__in=pks):
        ann.announcement_ptr.dismissals.get_or_create(user=user)
    del session[SESSION_KEY]
    session.save()
