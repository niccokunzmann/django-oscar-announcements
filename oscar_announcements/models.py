from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pinax.announcements.models import Announcement as PinaxAnnouncement


class Announcement(PinaxAnnouncement):
    """Oscar-aware announcement extending pinax-announcements.

    Adds ``level`` (info/warning) and ``visibility`` (extensible via the
    :mod:`oscar_announcements.visibility` registry).  ``dismissal_type`` is
    always set to DISMISSAL_PERMANENT so every user's dismissal is persisted.
    """

    INFO = "info"
    WARNING = "warning"
    LEVEL_CHOICES = [
        (INFO, _("Info")),
        (WARNING, _("Warning")),
    ]

    level = models.CharField(
        _("level"),
        max_length=10,
        choices=LEVEL_CHOICES,
        default=INFO,
    )
    visibility = models.CharField(
        _("visibility"),
        max_length=50,
        default="registered",
        help_text=_("Which audience can see this announcement."),
    )

    class Meta:
        verbose_name = _("announcement")
        verbose_name_plural = _("announcements")

    def __str__(self):
        return self.content[:60]

    def dismiss_url(self):
        return reverse("oscar_announcements:dismiss", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.content[:50]
        self.dismissal_type = PinaxAnnouncement.DISMISSAL_PERMANENT
        self.site_wide = True
        super().save(*args, **kwargs)

    @classmethod
    def delete_expired_announcements(cls):
        """Delete every announcement whose publish_end is in the past.

        Returns the Django ``QuerySet.delete()`` result tuple ``(count, detail)``.
        """
        return cls.objects.filter(
            publish_end__isnull=False,
            publish_end__lt=timezone.now(),
        ).delete()

    @classmethod
    def active_for_user(cls, user, *, excluded_pks=()):
        """Return queryset of announcements visible to *user* that are not dismissed.

        ``excluded_pks`` — primary keys already dismissed via session; used for
        both authenticated users (merged with DB dismissals) and anonymous users
        (session is the only dismissal mechanism available).

        Anonymous users see announcements with ``visibility="everyone"`` only.
        """
        from .visibility import get_visible_visibilities

        now = timezone.now()
        base_qs = (
            cls.objects.filter(publish_start__lte=now)
            .filter(Q(publish_end__isnull=True) | Q(publish_end__gt=now))
            .exclude(pk__in=excluded_pks)
        )

        if not user.is_authenticated:
            return base_qs.filter(visibility="everyone")

        visible = get_visible_visibilities(user)
        if not visible:
            return cls.objects.none()

        return base_qs.filter(
            Q(visibility__in=visible) | Q(visibility="creator", creator_id=user.pk)
        ).exclude(dismissals__user_id=user.pk)
