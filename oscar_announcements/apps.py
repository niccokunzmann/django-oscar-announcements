from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OscarAnnouncementsConfig(AppConfig):
    name = "oscar_announcements"
    verbose_name = _("Announcements")

    def ready(self):
        from .visibility import register

        register(
            "registered",
            _("Registered users"),
            lambda user: user.is_authenticated,
        )
        register(
            "staff",
            _("Staff only"),
            lambda user: user.is_staff or user.is_superuser,
        )
        # "creator" is handled specially in active_for_user — visible only to
        # the user who created the announcement. Register it here so it appears
        # as a form choice. The lambda is never used for filtering.
        register(
            "creator",
            _("Creator only (preview)"),
            lambda user: False,
        )

