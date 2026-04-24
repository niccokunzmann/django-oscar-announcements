"""Tests for the announcements context processor."""

import pytest
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model

from oscar_announcements import visibility as vis_module
from oscar_announcements.context_processors import announcements
from oscar_announcements.models import Announcement

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_request(user, session=None):
    req = MagicMock()
    req.user = user
    req.session = session or {}
    return req


def _mock_user(authenticated=True, is_staff=False, is_superuser=False):
    u = MagicMock()
    u.is_authenticated = authenticated
    u.is_staff = is_staff
    u.is_superuser = is_superuser
    u.pk = -1
    return u


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _registry():
    vis_module._REGISTRY.clear()
    vis_module.register("registered", "Registered", lambda u: u.is_authenticated)
    vis_module.register("staff", "Staff only", lambda u: u.is_staff)
    vis_module.register("creator", "Creator only (preview)", lambda u: False)
    yield
    vis_module._REGISTRY.clear()


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnnouncementsContextProcessor:
    def test_anonymous_returns_empty(self):
        req = _mock_request(_mock_user(authenticated=False))
        result = announcements(req)
        assert result == {}

    def test_authenticated_user_gets_key(self):
        req = _mock_request(_mock_user(authenticated=True, is_staff=False))
        with patch("oscar_announcements.models.Announcement") as MockAnn:
            MockAnn.active_for_user.return_value = []
            result = announcements(req)
        assert "site_announcements" in result

    def test_creator_visibility_shown_to_creator(self, db):
        creator, _ = User.objects.get_or_create(username="cp_creator", defaults={"is_staff": True})
        ann = Announcement(content="Creator preview", visibility="creator", creator=creator)
        ann.save()

        req = _mock_request(creator)
        result = announcements(req)
        assert ann in result["site_announcements"]

    def test_creator_visibility_not_shown_to_others(self, db):
        creator, _ = User.objects.get_or_create(username="cp_creator2", defaults={"is_staff": True})
        ann = Announcement(content="Creator preview 2", visibility="creator", creator=creator)
        ann.save()

        other, _ = User.objects.get_or_create(username="cp_other", defaults={"is_staff": True})
        req = _mock_request(other)
        result = announcements(req)
        assert ann not in result.get("site_announcements", [])
