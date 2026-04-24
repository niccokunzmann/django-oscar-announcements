"""Tests for Announcement.active_for_user and visibility filtering."""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.utils import timezone
from pinax.announcements.models import Announcement as PinaxAnnouncement, Dismissal

from oscar_announcements.models import Announcement
from oscar_announcements import visibility as vis_module

User = get_user_model()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_user(authenticated=True, is_staff=False, is_superuser=False, **attrs):
    u = MagicMock()
    u.is_authenticated = authenticated
    u.is_staff = is_staff
    u.is_superuser = is_superuser
    u.pk = -1  # valid integer that won't match any real user in DB
    for k, v in attrs.items():
        setattr(u, k, v)
    return u


def _make(creator, **kwargs):
    defaults = dict(content="Test announcement", visibility="registered", level=Announcement.INFO)
    defaults.update(kwargs)
    ann = Announcement(creator=creator, **defaults)
    ann.save()
    return ann


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _registry():
    vis_module._REGISTRY.clear()
    vis_module.register("registered", "Registered", lambda u: u.is_authenticated)
    vis_module.register("staff", "Staff only", lambda u: u.is_staff or u.is_superuser)
    yield
    vis_module._REGISTRY.clear()


@pytest.fixture()
def admin_user(db):
    user, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True})
    return user


# ── Visibility registry tests ─────────────────────────────────────────────────

class TestVisibilityRegistry:
    def test_get_choices(self):
        choices = vis_module.get_choices()
        assert ("registered", "Registered") in choices
        assert ("staff", "Staff only") in choices

    def test_registered_user_sees_registered(self):
        user = _mock_user(authenticated=True, is_staff=False)
        assert "registered" in vis_module.get_visible_visibilities(user)
        assert "staff" not in vis_module.get_visible_visibilities(user)

    def test_staff_user_sees_both(self):
        user = _mock_user(authenticated=True, is_staff=True)
        visible = vis_module.get_visible_visibilities(user)
        assert "registered" in visible
        assert "staff" in visible

    def test_anonymous_sees_nothing(self):
        user = _mock_user(authenticated=False, is_staff=False)
        assert vis_module.get_visible_visibilities(user) == []

    def test_extension_with_custom_level(self):
        vis_module.register("verified", "Verified", lambda u: getattr(u, "is_verified", False))
        user = _mock_user(authenticated=True, is_staff=False, is_verified=True)
        assert "verified" in vis_module.get_visible_visibilities(user)
        user2 = _mock_user(authenticated=True, is_staff=False, is_verified=False)
        assert "verified" not in vis_module.get_visible_visibilities(user2)


# ── active_for_user tests ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestActiveForUser:
    def test_anonymous_gets_empty_queryset(self):
        user = _mock_user(authenticated=False)
        assert Announcement.active_for_user(user).count() == 0

    def test_registered_user_sees_registered_announcement(self, admin_user):
        ann = _make(admin_user, visibility="registered")
        user = _mock_user(authenticated=True, is_staff=False)
        assert ann in list(Announcement.active_for_user(user))

    def test_registered_user_cannot_see_staff_announcement(self, admin_user):
        ann = _make(admin_user, visibility="staff")
        user = _mock_user(authenticated=True, is_staff=False)
        assert ann not in list(Announcement.active_for_user(user))

    def test_staff_user_sees_staff_announcement(self, admin_user):
        ann = _make(admin_user, visibility="staff")
        user = _mock_user(authenticated=True, is_staff=True)
        assert ann in list(Announcement.active_for_user(user))

    def test_expired_announcement_not_shown(self, admin_user):
        ann = _make(admin_user, publish_end=timezone.now() - timedelta(hours=1))
        user = _mock_user(authenticated=True, is_staff=False)
        assert ann not in list(Announcement.active_for_user(user))

    def test_future_start_not_shown(self, admin_user):
        ann = _make(admin_user)
        ann.publish_start = timezone.now() + timedelta(hours=1)
        ann.save()
        user = _mock_user(authenticated=True, is_staff=False)
        assert ann not in list(Announcement.active_for_user(user))

    def test_excluded_pks_skipped(self, admin_user):
        ann = _make(admin_user)
        user = _mock_user(authenticated=True, is_staff=False)
        assert ann not in list(Announcement.active_for_user(user, excluded_pks=[ann.pk]))

    def test_dismissed_announcement_not_shown(self, admin_user):
        ann = _make(admin_user)
        real_user, _ = User.objects.get_or_create(username="testuser")
        Dismissal.objects.create(user=real_user, announcement=ann.announcement_ptr)
        assert ann not in list(Announcement.active_for_user(real_user))


# ── Model.save() defaults ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnnouncementSaveDefaults:
    def test_title_auto_set_from_content(self, admin_user):
        ann = _make(admin_user, content="Hello world")
        assert ann.title == "Hello world"

    def test_long_content_title_truncated(self, admin_user):
        ann = _make(admin_user, content="X" * 100)
        assert len(ann.title) <= 50

    def test_dismissal_type_always_permanent(self, admin_user):
        ann = _make(admin_user)
        assert ann.dismissal_type == PinaxAnnouncement.DISMISSAL_PERMANENT

    def test_site_wide_always_true(self, admin_user):
        ann = _make(admin_user)
        assert ann.site_wide is True
