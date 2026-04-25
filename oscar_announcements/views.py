from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from .models import Announcement
from .utils import SESSION_KEY


class AnnouncementDismissView(SingleObjectMixin, View):
    """Dismiss an announcement.

    Authenticated users: permanent DB dismissal (persists across sessions and
    devices).

    Anonymous users: session-based dismissal stored under
    ``request.session["excluded_announcements"]``.
    """

    model = Announcement

    def post(self, request, *args, **kwargs):
        announcement = self.get_object()

        if request.user.is_authenticated:
            announcement.announcement_ptr.dismissals.get_or_create(user=request.user)
        else:
            excluded = set(request.session.get(SESSION_KEY, []))
            excluded.add(announcement.pk)
            request.session[SESSION_KEY] = list(excluded)

        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if is_ajax:
            return JsonResponse({}, status=200)
        return HttpResponse(content=b"", status=200)
