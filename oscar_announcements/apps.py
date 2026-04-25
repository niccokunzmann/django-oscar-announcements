from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OscarAnnouncementsConfig(AppConfig):
    name = "oscar_announcements"
    verbose_name = _("Announcements")

    def ready(self):
        from .visibility import register

        try:
            from oscar.apps.customer.signals import user_logged_in
            from .utils import transfer_session_dismissals

            def _on_login(sender, request, user, **kwargs):
                if request is not None:
                    transfer_session_dismissals(user, request.session)

            user_logged_in.connect(_on_login)
        except ImportError:
            pass

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
        register(
            "everyone",
            _("Everyone (including anonymous visitors)"),
            lambda user: True,
        )
        # "creator" is handled specially in active_for_user — visible only to
        # the user who created the announcement. Register it here so it appears
        # as a form choice. The lambda is never used for filtering.
        register(
            "creator",
            _("Creator only (preview)"),
            lambda user: False,
        )
