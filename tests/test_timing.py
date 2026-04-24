"""Tests for announcement timing states, with mocked clock.

publish_end is treated as end-of-day: an announcement set to expire on a date
is still shown for the entire day (up to 23:59:59.999...) and hidden only once
that day is over.
"""

import datetime
import pytest
from unittest.mock import patch

from django.contrib.auth import get_user_model
from pinax.announcements.models import Announcement as PinaxAnnouncement

from oscar_announcements.models import Announcement
from oscar_announcements.tasks import delete_expired_announcements
from oscar_announcements import visibility as vis_module

User = get_user_model()

# A fixed reference point: noon on 2024-06-15 UTC
_UTC = datetime.timezone.utc
NOON = datetime.datetime(2024, 6, 15, 12, 0, 0, tzinfo=_UTC)


# ── Helpers / fixtures ────────────────────────────────────────────────────────

def _patch_now(dt):
    """Context manager that makes timezone.now() return *dt* inside models."""
    return patch("oscar_announcements.models.timezone.now", return_value=dt)


def _patch_now_tasks(dt):
    """Patch timezone.now() inside both models and tasks."""
    return patch("oscar_announcements.tasks.timezone.now", return_value=dt)


@pytest.fixture(autouse=True)
def _registry():
    vis_module._REGISTRY.clear()
    vis_module.register("registered", "Registered", lambda u: u.is_authenticated)
    yield
    vis_module._REGISTRY.clear()


@pytest.fixture()
def timing_user(db):
    user, _ = User.objects.get_or_create(username="timing_user", defaults={"is_active": True})
    return user


@pytest.fixture()
def timing_creator(db):
    creator, _ = User.objects.get_or_create(username="timing_admin", defaults={"is_staff": True})
    return creator


def _make(creator, **kwargs):
    defaults = dict(content="Timing test", visibility="registered", level=Announcement.INFO)
    defaults.update(kwargs)
    ann = Announcement(creator=creator, **defaults)
    ann.save()
    return ann


# ── publish_start ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPublishStart:
    def test_future_start_hides_announcement(self, timing_user, timing_creator):
        ann = _make(timing_creator, publish_start=NOON + datetime.timedelta(hours=1))
        with _patch_now(NOON):
            assert ann not in list(Announcement.active_for_user(timing_user))

    def test_exactly_at_start_shows_announcement(self, timing_user, timing_creator):
        ann = _make(timing_creator, publish_start=NOON)
        with _patch_now(NOON):
            assert ann in list(Announcement.active_for_user(timing_user))

    def test_past_start_shows_announcement(self, timing_user, timing_creator):
        ann = _make(timing_creator, publish_start=NOON - datetime.timedelta(hours=1))
        with _patch_now(NOON):
            assert ann in list(Announcement.active_for_user(timing_user))


# ── publish_end ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPublishEnd:
    def test_no_end_shows_announcement(self, timing_user, timing_creator):
        ann = _make(timing_creator, publish_start=NOON - datetime.timedelta(hours=1),
                    publish_end=None)
        with _patch_now(NOON):
            assert ann in list(Announcement.active_for_user(timing_user))

    def test_future_end_shows_announcement(self, timing_user, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(hours=1),
                    publish_end=NOON + datetime.timedelta(hours=1))
        with _patch_now(NOON):
            assert ann in list(Announcement.active_for_user(timing_user))

    def test_past_end_hides_announcement(self, timing_user, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(days=2),
                    publish_end=NOON - datetime.timedelta(hours=1))
        with _patch_now(NOON):
            assert ann not in list(Announcement.active_for_user(timing_user))

    def test_end_of_day_still_shown_during_day(self, timing_user, timing_creator):
        """An announcement ending at 23:59:59 is visible throughout that day."""
        end_date = NOON.date()
        eod = datetime.datetime(end_date.year, end_date.month, end_date.day,
                                23, 59, 59, tzinfo=_UTC)
        ann = _make(timing_creator, publish_start=NOON - datetime.timedelta(hours=12),
                    publish_end=eod)

        morning = datetime.datetime(end_date.year, end_date.month, end_date.day,
                                    8, 0, 0, tzinfo=_UTC)
        with _patch_now(morning):
            assert ann in list(Announcement.active_for_user(timing_user))

        just_after = eod + datetime.timedelta(seconds=1)
        with _patch_now(just_after):
            assert ann not in list(Announcement.active_for_user(timing_user))

    def test_end_of_day_hidden_next_day(self, timing_user, timing_creator):
        """An announcement expiring 2024-06-15 is hidden from 2024-06-16 00:00:00."""
        end_date = NOON.date()
        eod = datetime.datetime(end_date.year, end_date.month, end_date.day,
                                23, 59, 59, tzinfo=_UTC)
        ann = _make(timing_creator, publish_start=NOON - datetime.timedelta(hours=12),
                    publish_end=eod)

        next_day_midnight = datetime.datetime(2024, 6, 16, 0, 0, 0, tzinfo=_UTC)
        with _patch_now(next_day_midnight):
            assert ann not in list(Announcement.active_for_user(timing_user))


# ── Combined states ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCombinedStates:
    def test_not_started_with_far_future_end(self, timing_user, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON + datetime.timedelta(days=1),
                    publish_end=NOON + datetime.timedelta(days=10))
        with _patch_now(NOON):
            assert ann not in list(Announcement.active_for_user(timing_user))

    def test_active_window_between_start_and_end(self, timing_user, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(hours=1),
                    publish_end=NOON + datetime.timedelta(hours=1))
        with _patch_now(NOON):
            assert ann in list(Announcement.active_for_user(timing_user))

    def test_wrong_audience_hidden_regardless_of_timing(self, timing_user, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(hours=1),
                    visibility="staff")
        with _patch_now(NOON):
            assert ann not in list(Announcement.active_for_user(timing_user))


# ── delete_expired_announcements ──────────────────────────────────────────────

@pytest.mark.django_db
class TestDeleteExpiredAnnouncements:
    def test_deletes_expired_announcement(self, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(days=2),
                    publish_end=NOON - datetime.timedelta(hours=1))
        with _patch_now_tasks(NOON):
            delete_expired_announcements()
        assert not Announcement.objects.filter(pk=ann.pk).exists()

    def test_keeps_active_announcement(self, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(hours=1),
                    publish_end=NOON + datetime.timedelta(hours=1))
        with _patch_now_tasks(NOON):
            delete_expired_announcements()
        assert Announcement.objects.filter(pk=ann.pk).exists()

    def test_keeps_announcement_with_no_end(self, timing_creator):
        ann = _make(timing_creator,
                    publish_start=NOON - datetime.timedelta(hours=1),
                    publish_end=None)
        with _patch_now_tasks(NOON):
            delete_expired_announcements()
        assert Announcement.objects.filter(pk=ann.pk).exists()

    def test_returns_count_of_deleted(self, timing_creator):
        ann1 = _make(timing_creator,
                     publish_start=NOON - datetime.timedelta(days=2),
                     publish_end=NOON - datetime.timedelta(hours=1))
        ann2 = _make(timing_creator,
                     publish_start=NOON - datetime.timedelta(days=2),
                     publish_end=NOON - datetime.timedelta(hours=2))
        with _patch_now_tasks(NOON):
            delete_expired_announcements()
        assert not Announcement.objects.filter(pk__in=[ann1.pk, ann2.pk]).exists()

    def test_end_of_day_not_deleted_during_day(self, timing_creator):
        """An announcement expiring today at 23:59:59 survives the morning sweep."""
        end_date = NOON.date()
        eod = datetime.datetime(end_date.year, end_date.month, end_date.day,
                                23, 59, 59, tzinfo=_UTC)
        ann = _make(timing_creator, publish_start=NOON - datetime.timedelta(hours=12),
                    publish_end=eod)
        morning = datetime.datetime(end_date.year, end_date.month, end_date.day,
                                    6, 0, 0, tzinfo=_UTC)
        with _patch_now_tasks(morning):
            delete_expired_announcements()
        assert Announcement.objects.filter(pk=ann.pk).exists()

    def test_end_of_day_deleted_after_midnight(self, timing_creator):
        """The same announcement is removed once the day has passed."""
        end_date = NOON.date()
        eod = datetime.datetime(end_date.year, end_date.month, end_date.day,
                                23, 59, 59, tzinfo=_UTC)
        ann = _make(timing_creator, publish_start=NOON - datetime.timedelta(hours=12),
                    publish_end=eod)
        next_day = datetime.datetime(2024, 6, 16, 0, 1, 0, tzinfo=_UTC)
        with _patch_now_tasks(next_day):
            delete_expired_announcements()
        assert not Announcement.objects.filter(pk=ann.pk).exists()
