"""Tests for dashboard views and the public dismiss endpoint."""

import pytest
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import Client, RequestFactory
from pinax.announcements.models import Dismissal

from oscar_announcements import visibility as vis_module
from oscar_announcements.dashboard.views import (
    AnnouncementCreateView,
    AnnouncementListView,
    AnnouncementUpdateView,
)
from oscar_announcements.models import Announcement

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _registry():
    vis_module._REGISTRY.clear()
    vis_module.register("registered", "Registered", lambda u: u.is_authenticated)
    vis_module.register("staff", "Staff only", lambda u: u.is_staff)
    yield
    vis_module._REGISTRY.clear()


@pytest.fixture()
def staff_user(db):
    u, _ = User.objects.get_or_create(
        username="staff_view", defaults={"is_staff": True, "is_active": True}
    )
    u.set_unusable_password()
    u.save()
    return u


@pytest.fixture()
def regular_user(db):
    u, _ = User.objects.get_or_create(
        username="regular_view", defaults={"is_staff": False, "is_active": True}
    )
    u.set_unusable_password()
    u.save()
    return u


def _make(creator, content="Hello", visibility="registered", **kwargs):
    ann = Announcement(content=content, visibility=visibility, creator=creator, **kwargs)
    ann.save()
    return ann


# ── Dismiss view ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDismissView:
    def test_ajax_dismiss_returns_200(self, staff_user):
        ann = _make(staff_user, visibility="staff")
        client = Client()
        client.force_login(staff_user)
        resp = client.post(
            f"/announcements/{ann.pk}/dismiss/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_dismiss_removes_from_active(self, staff_user):
        ann = _make(staff_user, visibility="staff")
        client = Client()
        client.force_login(staff_user)
        client.post(
            f"/announcements/{ann.pk}/dismiss/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert not Announcement.active_for_user(staff_user).filter(pk=ann.pk).exists()

    def test_dismiss_requires_post(self, staff_user):
        ann = _make(staff_user)
        client = Client()
        client.force_login(staff_user)
        resp = client.get(f"/announcements/{ann.pk}/dismiss/")
        assert resp.status_code == 405


# ── Dashboard view access ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDashboardViewAccess:
    def test_unauthenticated_redirected_from_list(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = MagicMock(is_authenticated=False, is_staff=False, is_superuser=False)
        resp = AnnouncementListView.as_view()(request)
        assert resp.status_code == 302

    def test_authenticated_non_staff_raises_permission_denied(self, regular_user):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = regular_user
        with pytest.raises(PermissionDenied):
            AnnouncementListView.as_view()(request)

    def test_list_allowed_for_staff(self, staff_user):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = staff_user
        with patch.object(
            AnnouncementListView,
            "render_to_response",
            return_value=HttpResponse("ok"),
        ):
            response = AnnouncementListView.as_view()(request)
        assert response.status_code == 200


# ── Create view ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnnouncementCreate:
    def test_form_valid_creates_object(self, staff_user):
        factory = RequestFactory()
        request = factory.post("/", {
            "content": "Brand new announcement",
            "level": "info",
            "visibility": "registered",
            "publish_end": "",
            "clear_dismissals": "",
        })
        request.user = staff_user

        with patch("oscar_announcements.dashboard.views.messages"):
            with patch.object(AnnouncementCreateView, "get_success_url", return_value="/"):
                response = AnnouncementCreateView.as_view()(request)

        assert response.status_code == 302
        assert Announcement.objects.filter(content="Brand new announcement").exists()
        ann = Announcement.objects.get(content="Brand new announcement")
        assert ann.creator == staff_user


# ── Clear dismissals ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestClearDismissals:
    def test_clear_dismissals_deletes_records(self, staff_user):
        ann = _make(staff_user)
        Dismissal.objects.create(user=staff_user, announcement=ann.announcement_ptr)
        assert ann.announcement_ptr.dismissals.count() == 1

        factory = RequestFactory()
        request = factory.post("/", {
            "content": ann.content,
            "level": ann.level,
            "visibility": ann.visibility,
            "publish_end": "",
            "clear_dismissals": "on",
        })
        request.user = staff_user

        with patch("oscar_announcements.dashboard.views.messages"):
            with patch.object(AnnouncementUpdateView, "get_success_url", return_value="/"):
                AnnouncementUpdateView.as_view()(request, pk=ann.pk)

        assert ann.announcement_ptr.dismissals.count() == 0


