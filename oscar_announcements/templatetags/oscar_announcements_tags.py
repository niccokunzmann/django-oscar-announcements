"""Template tags for rendering site announcements.

Usage in any template::

    {% load oscar_announcements_tags %}

    {# Render all active announcements for the current user: #}
    {% render_announcements %}

    {# Or loop manually for a custom layout: #}
    {% get_announcements as my_announcements %}
    {% for ann in my_announcements %}
        ...
    {% endfor %}

``render_announcements`` renders ``oscar_announcements/partials/announcements.html``
using the ``site_announcements`` already injected by the context processor.
If the context processor is not installed, it falls back to a fresh queryset.
"""

from django import template
from django.template.loader import render_to_string

from oscar_announcements.models import Announcement

register = template.Library()


class AnnouncementsNode(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        announcements = context.get("site_announcements")
        if announcements is None:
            request = context.get("request")
            if request and request.user.is_authenticated:
                excluded = set(request.session.get("excluded_announcements", []))
                announcements = list(
                    Announcement.active_for_user(request.user, excluded_pks=excluded)
                )
            else:
                announcements = []
        context[self.var_name] = announcements
        return ""


@register.tag
def get_announcements(parser, token):
    """Assign the active announcements list to a template variable.

    Usage::

        {% get_announcements as my_var %}
    """
    bits = token.split_contents()
    if len(bits) != 3 or bits[1] != "as":
        raise template.TemplateSyntaxError(
            "Usage: {% get_announcements as <var_name> %}"
        )
    return AnnouncementsNode(var_name=bits[2])


@register.inclusion_tag(
    "oscar_announcements/partials/announcements.html", takes_context=True
)
def render_announcements(context):
    """Render the announcements banner.

    Uses ``site_announcements`` from the template context (populated by the
    context processor) or fetches it from the database as a fallback.

    Include once in the base template, typically just before ``<main>`` or
    at the top of the page content::

        {% load oscar_announcements_tags %}
        {% render_announcements %}
    """
    announcements = context.get("site_announcements")
    if announcements is None:
        request = context.get("request")
        if request and request.user.is_authenticated:
            excluded = set(request.session.get("excluded_announcements", []))
            announcements = list(
                Announcement.active_for_user(request.user, excluded_pks=excluded)
            )
        else:
            announcements = []
    return {"site_announcements": announcements, "request": context.get("request")}
