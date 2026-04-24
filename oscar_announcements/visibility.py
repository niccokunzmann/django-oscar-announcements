"""Registry mapping visibility names to user-predicate callables.

Host applications extend this by calling ``register()`` in their ``AppConfig.ready()``.

Example (adding a "verified" audience)::

    from oscar_announcements.visibility import register
    register("verified", _("Verified users"), lambda user: getattr(user, "is_verified", False))
"""

from typing import Callable

_REGISTRY: dict[str, tuple[str, Callable]] = {}


def register(name: str, label: str, handler: Callable) -> None:
    """Register a visibility level.

    :param name: Machine-readable key stored on ``Announcement.visibility``.
    :param label: Human-readable label shown in the dashboard form.
    :param handler: ``(user) -> bool`` — returns True when *user* is eligible.
    """
    _REGISTRY[name] = (label, handler)


def get_choices() -> list[tuple[str, str]]:
    """Return form choices for the visibility field."""
    return [(name, label) for name, (label, _) in _REGISTRY.items()]


def get_visible_visibilities(user) -> list[str]:
    """Return visibility names that apply to *user*."""
    return [name for name, (_, handler) in _REGISTRY.items() if handler(user)]
