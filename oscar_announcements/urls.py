"""Public URL — dismiss endpoint.

Include with a namespace::

    path("announcements/", include("oscar_announcements.urls", namespace="oscar_announcements")),

The dismiss view is pinax's built-in ``AnnouncementDismissView`` which handles
both AJAX (returns JSON) and plain-form POST (returns empty 200).
"""

from django.urls import re_path
from pinax.announcements.views import AnnouncementDismissView

app_name = "oscar_announcements"

urlpatterns = [
    re_path(
        r"^(?P<pk>\d+)/dismiss/$",
        AnnouncementDismissView.as_view(),
        name="dismiss",
    ),
]
