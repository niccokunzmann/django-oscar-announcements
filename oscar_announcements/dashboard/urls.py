from django.urls import path, re_path

from .views import (
    AnnouncementCreateView,
    AnnouncementDeleteView,
    AnnouncementListView,
    AnnouncementUpdateView,
)

urlpatterns = [
    path("announcements/", AnnouncementListView.as_view(), name="announcement-list"),
    path("announcements/create/", AnnouncementCreateView.as_view(), name="announcement-create"),
    re_path(r"announcements/(?P<pk>\d+)/edit/$", AnnouncementUpdateView.as_view(), name="announcement-edit"),
    re_path(r"announcements/(?P<pk>\d+)/delete/$", AnnouncementDeleteView.as_view(), name="announcement-delete"),
]

permissions = {
    "announcement-list": ["is_staff"],
    "announcement-create": ["is_staff"],
    "announcement-edit": ["is_staff"],
    "announcement-delete": ["is_staff"],
}
