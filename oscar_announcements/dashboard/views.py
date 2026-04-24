from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, Q, Value, When
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from oscar_announcements.models import Announcement
from .forms import AnnouncementForm


class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AnnouncementListView(StaffRequiredMixin, ListView):
    model = Announcement
    template_name = "oscar_announcements/dashboard/announcement_list.html"
    context_object_name = "announcements"

    def get_queryset(self):
        now = timezone.now()
        # Sort: active (0) → upcoming (1) → expired (2), then by publish_start within each group
        return Announcement.objects.annotate(
            _status_order=Case(
                When(Q(publish_start__lte=now) & (Q(publish_end__isnull=True) | Q(publish_end__gt=now)), then=Value(0)),
                When(publish_start__gt=now, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).order_by("_status_order", "publish_start")

    def get_context_data(self, **kwargs):
        return super().get_context_data(now=timezone.now(), **kwargs)


class AnnouncementCreateView(StaffRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "oscar_announcements/dashboard/announcement_form.html"
    success_url = reverse_lazy("dashboard:announcement-list")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.success(self.request, _("Announcement created."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(title=_("Create Announcement"), **kwargs)


class AnnouncementUpdateView(StaffRequiredMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "oscar_announcements/dashboard/announcement_form.html"
    success_url = reverse_lazy("dashboard:announcement-list")

    def form_valid(self, form):
        messages.success(self.request, _("Announcement updated."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(title=_("Edit Announcement"), **kwargs)


class AnnouncementDeleteView(StaffRequiredMixin, DeleteView):
    model = Announcement
    template_name = "oscar_announcements/dashboard/announcement_confirm_delete.html"
    success_url = reverse_lazy("dashboard:announcement-list")

    def form_valid(self, form):
        messages.success(self.request, _("Announcement deleted."))
        return super().form_valid(form)
