"""Public URL — dismiss endpoint.

Include with a namespace::

    path("announcements/", include("oscar_announcements.urls", namespace="oscar_announcements")),
"""

from django.urls import re_path

from .views import AnnouncementDismissView

app_name = "oscar_announcements"

urlpatterns = [
    re_path(
        r"^(?P<pk>\d+)/dismiss/$",
        AnnouncementDismissView.as_view(),
        name="dismiss",
    ),
]
