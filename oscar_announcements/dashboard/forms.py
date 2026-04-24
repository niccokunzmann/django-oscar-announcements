from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pinax.announcements.models import Announcement as PinaxAnnouncement

from oscar_announcements.models import Announcement
from oscar_announcements.visibility import get_choices

_DATETIME_WIDGET = forms.DateTimeInput(
    attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
)


class AnnouncementForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        label=_("Message"),
        help_text=_("HTML is supported — you can add links, bold text, etc."),
    )
    visibility = forms.ChoiceField(
        choices=get_choices,
        label=_("Audience"),
        help_text=_(
            "Who will see this announcement."
        ),
    )
    clear_dismissals = forms.BooleanField(
        required=False,
        label=_("Substantial edit — re-send to all users"),
        help_text=_(
            "Check this if the edit is significant enough that users who "
            "already dismissed it should see it again."
        ),
    )

    class Meta:
        model = Announcement
        fields = ["content", "level", "visibility", "publish_start", "publish_end"]
        widgets = {
            "publish_start": _DATETIME_WIDGET,
            "publish_end": _DATETIME_WIDGET,
        }
        labels = {
            "level": _("Type"),
            "publish_start": _("Show from"),
            "publish_end": _("Expires at"),
        }
        help_texts = {
            "publish_start": _("Leave blank to show immediately."),
            "publish_end": _("Leave blank to never expire."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # publish_start is not nullable on the pinax model; make it optional in
        # the form and fall back to now() in save().
        self.fields["publish_start"].required = False

    def clean_publish_end(self):
        dt = self.cleaned_data.get("publish_end")
        if dt is None:
            return None
        # Treat the expiry date as end-of-day so the announcement is still
        # visible throughout the chosen day.
        return dt.replace(hour=23, minute=59, second=59, microsecond=0)

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.title = obj.content[:50]
        obj.dismissal_type = PinaxAnnouncement.DISMISSAL_PERMANENT
        obj.site_wide = True
        if not obj.publish_start:
            obj.publish_start = timezone.now()
        if commit:
            obj.save()
            if self.cleaned_data.get("clear_dismissals"):
                obj.announcement_ptr.dismissals.all().delete()
        return obj
