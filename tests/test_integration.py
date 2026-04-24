"""Full HTTP integration tests using Django test Client.

These tests exercise the complete request/response cycle including middleware,
URL routing, view logic, form processing, and template rendering.
"""

import datetime
import pytest
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from pinax.announcements.models import Dismissal

from oscar_announcements import visibility as vis_module
from oscar_announcements.context_processors import announcements as announcements_ctx
from oscar_announcements.models import Announcement

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _registry():
    vis_module._REGISTRY.clear()
    vis_module.register("registered", "Registered", lambda u: u.is_authenticated)
    vis_module.register("staff", "Staff only", lambda u: u.is_staff)
    vis_module.register("creator", "Creator only (preview)", lambda u: False)
    yield
    vis_module._REGISTRY.clear()


@pytest.fixture()
def staff(db):
    u, _ = User.objects.get_or_create(
        username="int_staff", defaults={"is_staff": True, "is_active": True}
    )
    u.set_password("pass")
    u.save()
    return u


@pytest.fixture()
def member(db):
    u, _ = User.objects.get_or_create(
        username="int_member", defaults={"is_staff": False, "is_active": True}
    )
    u.set_password("pass")
    u.save()
    return u


@pytest.fixture()
def other_staff(db):
    u, _ = User.objects.get_or_create(
        username="int_other_staff", defaults={"is_staff": True, "is_active": True}
    )
    u.set_password("pass")
    u.save()
    return u


@pytest.fixture()
def staff_client(staff):
    c = Client()
    c.force_login(staff)
    return c


@pytest.fixture()
def member_client(member):
    c = Client()
    c.force_login(member)
    return c


def _make(creator, **kwargs):
    defaults = dict(content="Integration test", visibility="registered", level=Announcement.INFO)
    defaults.update(kwargs)
    ann = Announcement(creator=creator, **defaults)
    ann.save()
    return ann


def _mock_request(user, session=None):
    req = MagicMock()
    req.user = user
    req.session = session or {}
    return req


# ── Dashboard access control ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestDashboardAccess:
    def test_unauthenticated_redirected_from_list(self):
        resp = Client().get("/dashboard/announcements/")
        assert resp.status_code == 302

    def test_non_staff_redirected_from_list(self, member_client):
        resp = member_client.get("/dashboard/announcements/")
        assert resp.status_code in (302, 403)

    def test_staff_can_access_list(self, staff_client):
        resp = staff_client.get("/dashboard/announcements/")
        assert resp.status_code == 200

    def test_staff_can_access_create_form(self, staff_client):
        resp = staff_client.get("/dashboard/announcements/create/")
        assert resp.status_code == 200

    def test_non_staff_redirected_from_create(self, member_client):
        resp = member_client.get("/dashboard/announcements/create/")
        assert resp.status_code in (302, 403)


# ── Create ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateAnnouncement:
    def test_post_creates_announcement(self, staff_client):
        resp = staff_client.post("/dashboard/announcements/create/", {
            "content": "Hello world integration",
            "level": "info",
            "visibility": "registered",
            "publish_end": "",
        })
        assert resp.status_code == 302
        assert Announcement.objects.filter(content="Hello world integration").exists()

    def test_created_announcement_has_correct_fields(self, staff_client, staff):
        staff_client.post("/dashboard/announcements/create/", {
            "content": "My new announcement",
            "level": "warning",
            "visibility": "staff",
            "publish_end": "",
        })
        ann = Announcement.objects.get(content="My new announcement")
        assert ann.level == "warning"
        assert ann.visibility == "staff"
        assert ann.creator == staff
        assert ann.site_wide is True

    def test_html_content_is_accepted_and_preserved(self, staff_client):
        html = '<p>Hello <a href="https://example.com"><strong>world</strong></a></p>'
        staff_client.post("/dashboard/announcements/create/", {
            "content": html,
            "level": "info",
            "visibility": "registered",
            "publish_end": "",
        })
        ann = Announcement.objects.get(content=html)
        assert ann.content == html

    def test_invalid_form_returns_200(self, staff_client):
        resp = staff_client.post("/dashboard/announcements/create/", {
            "content": "",  # required
            "level": "info",
            "visibility": "registered",
        })
        assert resp.status_code == 200


# ── Update ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUpdateAnnouncement:
    def test_edit_form_loads(self, staff_client, staff):
        ann = _make(staff)
        resp = staff_client.get(f"/dashboard/announcements/{ann.pk}/edit/")
        assert resp.status_code == 200

    def test_post_updates_content(self, staff_client, staff):
        ann = _make(staff, content="Original")
        staff_client.post(f"/dashboard/announcements/{ann.pk}/edit/", {
            "content": "Updated content",
            "level": ann.level,
            "visibility": ann.visibility,
            "publish_end": "",
        })
        ann.refresh_from_db()
        assert ann.content == "Updated content"

    def test_clear_dismissals_on_edit(self, staff_client, staff):
        ann = _make(staff)
        Dismissal.objects.create(user=staff, announcement=ann.announcement_ptr)
        assert ann.announcement_ptr.dismissals.count() == 1

        staff_client.post(f"/dashboard/announcements/{ann.pk}/edit/", {
            "content": ann.content,
            "level": ann.level,
            "visibility": ann.visibility,
            "publish_end": "",
            "clear_dismissals": "on",
        })
        assert ann.announcement_ptr.dismissals.count() == 0


# ── Delete ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDeleteAnnouncement:
    def test_delete_confirm_page_loads(self, staff_client, staff):
        ann = _make(staff)
        resp = staff_client.get(f"/dashboard/announcements/{ann.pk}/delete/")
        assert resp.status_code == 200

    def test_post_deletes_announcement(self, staff_client, staff):
        ann = _make(staff)
        pk = ann.pk
        staff_client.post(f"/dashboard/announcements/{ann.pk}/delete/")
        assert not Announcement.objects.filter(pk=pk).exists()

    def test_delete_redirects_to_list(self, staff_client, staff):
        ann = _make(staff)
        resp = staff_client.post(f"/dashboard/announcements/{ann.pk}/delete/")
        assert resp.status_code == 302
        assert "/dashboard/announcements/" in resp["Location"]


# ── Dismiss ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDismissEndpoint:
    def test_ajax_dismiss_returns_json_200(self, member_client, staff):
        ann = _make(staff, visibility="registered")
        resp = member_client.post(
            f"/announcements/{ann.pk}/dismiss/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_form_dismiss_returns_200(self, member_client, staff):
        ann = _make(staff, visibility="registered")
        resp = member_client.post(f"/announcements/{ann.pk}/dismiss/")
        assert resp.status_code == 200

    def test_get_dismiss_not_allowed(self, member_client, staff):
        ann = _make(staff)
        resp = member_client.get(f"/announcements/{ann.pk}/dismiss/")
        assert resp.status_code == 405

    def test_dismiss_creates_dismissal_record(self, member_client, member, staff):
        ann = _make(staff, visibility="registered")
        member_client.post(
            f"/announcements/{ann.pk}/dismiss/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert Dismissal.objects.filter(user=member, announcement=ann.announcement_ptr).exists()

    def test_dismissed_announcement_not_shown_to_user(self, member_client, member, staff):
        ann = _make(staff, visibility="registered")
        member_client.post(
            f"/announcements/{ann.pk}/dismiss/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert not Announcement.active_for_user(member).filter(pk=ann.pk).exists()


# ── dismiss_url property ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDismissUrl:
    def test_dismiss_url_uses_oscar_namespace(self, staff):
        ann = _make(staff)
        assert ann.dismiss_url() == f"/announcements/{ann.pk}/dismiss/"


# ── Creator visibility ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreatorVisibility:
    """visibility='creator' acts as a personal preview: only the creator sees it."""

    def test_creator_sees_own_announcement(self, staff):
        ann = _make(staff, visibility="creator")
        req = _mock_request(staff)
        ctx = announcements_ctx(req)
        assert ann in ctx["site_announcements"]

    def test_other_staff_cannot_see_creator_announcement(self, staff, other_staff):
        ann = _make(staff, visibility="creator")
        req = _mock_request(other_staff)
        ctx = announcements_ctx(req)
        assert ann not in ctx.get("site_announcements", [])

    def test_regular_user_cannot_see_creator_announcement(self, staff, member):
        ann = _make(staff, visibility="creator")
        req = _mock_request(member)
        ctx = announcements_ctx(req)
        assert ann not in ctx.get("site_announcements", [])

    def test_creator_announcement_subject_to_publish_dates(self, staff):
        """Creator announcements still respect publish_start."""
        future = timezone.now() + datetime.timedelta(days=5)
        ann = _make(staff, visibility="creator", publish_start=future)
        req = _mock_request(staff)
        ctx = announcements_ctx(req)
        assert ann not in ctx.get("site_announcements", [])

    def test_creator_announcement_dismissable(self, staff_client, staff):
        ann = _make(staff, visibility="creator")
        staff_client.post(
            f"/announcements/{ann.pk}/dismiss/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert not Announcement.active_for_user(staff).filter(pk=ann.pk).exists()

    def test_creator_visibility_appears_in_form_choices(self):
        from oscar_announcements.visibility import get_choices
        assert any(k == "creator" for k, _ in get_choices())


# ── List view ordering ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListViewOrdering:
    """Active announcements first, upcoming second, expired last."""

    def _make(self, creator, **kwargs):
        defaults = dict(content="List order test", visibility="registered", level=Announcement.INFO)
        defaults.update(kwargs)
        ann = Announcement(creator=creator, **defaults)
        ann.save()
        return ann

    def test_active_appears_before_upcoming(self, staff_client, staff):
        now = timezone.now()
        upcoming = self._make(staff, content="Upcoming", publish_start=now + datetime.timedelta(days=1))
        active = self._make(staff, content="Active", publish_start=now - datetime.timedelta(hours=1))

        resp = staff_client.get("/dashboard/announcements/")
        assert resp.status_code == 200
        announcements = list(resp.context["announcements"])
        assert announcements.index(active) < announcements.index(upcoming)

    def test_upcoming_appears_before_expired(self, staff_client, staff):
        now = timezone.now()
        expired = self._make(
            staff, content="Expired",
            publish_start=now - datetime.timedelta(days=2),
            publish_end=now - datetime.timedelta(hours=1),
        )
        upcoming = self._make(staff, content="Upcoming", publish_start=now + datetime.timedelta(days=1))

        resp = staff_client.get("/dashboard/announcements/")
        assert resp.status_code == 200
        announcements = list(resp.context["announcements"])
        assert announcements.index(upcoming) < announcements.index(expired)

    def test_active_appears_before_expired(self, staff_client, staff):
        now = timezone.now()
        expired = self._make(
            staff, content="Expired",
            publish_start=now - datetime.timedelta(days=2),
            publish_end=now - datetime.timedelta(hours=1),
        )
        active = self._make(staff, content="Active", publish_start=now - datetime.timedelta(hours=1))

        resp = staff_client.get("/dashboard/announcements/")
        assert resp.status_code == 200
        announcements = list(resp.context["announcements"])
        assert announcements.index(active) < announcements.index(expired)

    def test_full_order_active_upcoming_expired(self, staff_client, staff):
        now = timezone.now()
        expired = self._make(
            staff, content="Expired",
            publish_start=now - datetime.timedelta(days=2),
            publish_end=now - datetime.timedelta(hours=1),
        )
        upcoming = self._make(staff, content="Upcoming", publish_start=now + datetime.timedelta(days=1))
        active = self._make(staff, content="Active", publish_start=now - datetime.timedelta(hours=1))

        resp = staff_client.get("/dashboard/announcements/")
        assert resp.status_code == 200
        announcements = list(resp.context["announcements"])
        assert announcements.index(active) < announcements.index(upcoming) < announcements.index(expired)
