# django-oscar-announcements

Staff-managed site-wide announcements for [Django Oscar](https://github.com/django-oscar/django-oscar), built on top of [pinax-announcements](https://github.com/pinax/pinax-announcements).

Features:

* Dashboard CRUD (Customers → Announcements)
* **Info** (blue) and **Warning** (red) levels that match Oscar/Bootstrap alert colours
* Extensible **visibility** — built-in *Registered* and *Staff* audiences; add your own (e.g. *Verified*)
* AJAX dismiss with **no-JS form fallback**
* **Test** button — preview an announcement on the public site without publishing it
* **Re-send** checkbox — clear dismissals so users see it again after an edit
* Auto-delete via [django-background-tasks](https://github.com/arteria/django-background-tasks) when an expiry date passes

![](img/create-announcement.png)
![](img/new-announcement.png)

---

## Installation

```bash
pip install django-oscar-announcements   # or install editable from source
```

### 1. `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "pinax.announcements",   # required dependency
    "oscar_announcements",
    'background_task',
    ...
]
```

### 2. Context processor

Add to `TEMPLATES[0]["OPTIONS"]["context_processors"]`:

```python
"oscar_announcements.context_processors.announcements",
```

This populates `site_announcements` in every template context.

### 3. Public dismiss URL

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path(
        "announcements/",
        include("oscar_announcements.urls", namespace="oscar_announcements"),
    ),
]
```

### 4. Oscar dashboard

Wire the CRUD views into your Oscar `DashboardConfig`:

```python
# myapp/apps/dashboard/apps.py
from oscar.apps.dashboard.apps import DashboardConfig as OscarDashboardConfig
from django.urls import include, path


class DashboardConfig(OscarDashboardConfig):
    def configure_permissions(self):
        super().configure_permissions()
        from oscar_announcements.dashboard.urls import permissions as ann_permissions

        self.permissions_map.update(ann_permissions)

    def get_urls(self):
        from oscar_announcements.dashboard.urls import urlpatterns as ann_urls

        return super().get_urls() + self.post_process_urls(ann_urls)
```

Add a nav entry (Customers section is index 3 in default Oscar navigation):

```python
from django.utils.translation import gettext_lazy as _

OSCAR_DASHBOARD_NAVIGATION[3]["children"].append(
    {"label": _("Announcements"), "url_name": "dashboard:announcement-list"}
)
```

### 5. Templates — render announcements

Load the tag in any base template and call `{% render_announcements %}`:

```html
{% load oscar_announcements_tags %}

{# Public site (myco_layout.html, after flash messages): #}
{% render_announcements %}

{# Dashboard (e.g. inside {% block extrascripts %} or any layout block): #}
{% render_announcements %}
```

Add the JavaScript once (before `</body>`):

```html
{% load static %}
<script src="{% static 'oscar_announcements/js/announcements.js' %}"></script>
```

Add the CSS (only needed on non-Bootstrap pages; Oscar dashboard gets colours from Bootstrap):

```html
<link rel="stylesheet" href="{% static 'oscar_announcements/css/announcements.css' %}">
```

---

## Extending visibility

Register custom audience handlers in your app's `AppConfig.ready()`:

```python
# myapp/apps.py
from oscar_announcements.visibility import register
from django.utils.translation import gettext_lazy as _

class MyAppConfig(AppConfig):
    def ready(self):
        register(
            "verified",
            _("Verified users"),
            lambda user: getattr(user, "is_verified", False) or user.is_staff,
        )
```

The new option then appears automatically in the dashboard form's *Audience* dropdown.

---

## Template tags reference

```
{% load oscar_announcements_tags %}

# Render the built-in partial (oscar_announcements/partials/announcements.html):
{% render_announcements %}

# Assign the list to a variable for custom rendering:
{% get_announcements as my_announcements %}
{% for ann in my_announcements %}
    <p class="oa-announcement--{{ ann.level }}">{{ ann.content }}</p>
{% endfor %}
```

## Development

Setup:

```bash
git clone https://github.com/niccokunzmann/django-oscar-announcements
cd django-oscar-announcements
make dev
```

Run tests:

```bash
make test
```

Run the example:

```bash
cd example
make superuser # creates a superuser
make test # runs the tests
make run # runs the example
```

---

### Releases

Edit `CHANGES.md`.
Tag and push:

```bash
git tag v0.0.1
git push --follow-tags
```
