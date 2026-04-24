"""Minimal URL configuration for package view tests."""

from django.http import HttpResponse
from django.urls import include, path

from oscar_announcements import urls as dismiss_urls
from oscar_announcements.dashboard import urls as dashboard_urls


def _dummy_index(request):
    return HttpResponse("Dashboard")


urlpatterns = [
    path("announcements/", include(dismiss_urls)),
    path("dashboard/", include(([
        path("", _dummy_index, name="index"),
        *dashboard_urls.urlpatterns,
    ], "dashboard"))),
]
