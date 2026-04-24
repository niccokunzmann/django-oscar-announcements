"""Cleanup task: delete all expired announcements in one daily sweep.

The plain function ``delete_expired_announcements`` can be called directly
(e.g. from tests or a management command).  The ``@background`` wrapper
schedules it to run once per day just after midnight and re-queues itself
automatically.

To kick off the first scheduled run, call::

    from oscar_announcements.tasks import schedule_daily_cleanup
    schedule_daily_cleanup()

or run the management command::

    python manage.py cleanup_announcements --schedule
"""

import datetime

from django.utils import timezone


def delete_expired_announcements():
    """Delete every announcement whose publish_end is in the past.

    Returns the Django ``QuerySet.delete()`` result tuple ``(count, detail)``.
    """
    from .models import Announcement

    return Announcement.objects.filter(
        publish_end__isnull=False,
        publish_end__lt=timezone.now(),
    ).delete()


def _next_midnight_seconds():
    """Seconds until just after midnight tonight (00:01:00 tomorrow)."""
    now = timezone.now()
    tomorrow = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0
    )
    return max(1, int((tomorrow - now).total_seconds()))


try:
    from background_task import background

    @background
    def _scheduled_expiry_cleanup():
        delete_expired_announcements()
        _scheduled_expiry_cleanup(schedule=_next_midnight_seconds())

    def schedule_daily_cleanup():
        """Queue the first daily cleanup if it is not already scheduled.

        Safe to call multiple times — idempotent.
        """
        from background_task.models import Task

        task_name = "oscar_announcements.tasks._scheduled_expiry_cleanup"
        if not Task.objects.filter(task_name=task_name).exists():
            _scheduled_expiry_cleanup(schedule=_next_midnight_seconds())

except ImportError:  # background_task not installed
    def schedule_daily_cleanup():  # noqa: F811
        pass
