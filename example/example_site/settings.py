import os
import oscar
from oscar.defaults import *  # noqa: F401,F403

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "example-insecure-key-do-not-use-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Replace oscar's built-in dashboard with our customised version
_apps = list(oscar.INSTALLED_APPS)
_apps[_apps.index("oscar.apps.dashboard.apps.DashboardConfig")] = (
    "example_site.apps.DashboardConfig"
)

# oscar_announcements must precede oscar.config.Shop so its
# oscar/dashboard/partials/alert_messages.html override is found first.
INSTALLED_APPS = [
    "pinax.announcements",
    "oscar_announcements",
    *_apps,
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oscar.apps.basket.middleware.BasketMiddleware",
]

ROOT_URLCONF = "example_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "example_site", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "oscar.apps.search.context_processors.search_form",
                "oscar.apps.checkout.context_processors.checkout",
                "oscar.apps.communication.notifications.context_processors.notifications",
                "oscar_announcements.context_processors.announcements",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")

AUTHENTICATION_BACKENDS = (
    "oscar.apps.customer.auth_backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
)

OSCAR_DEFAULT_CURRENCY = "GBP"

import copy  # noqa: E402
from oscar import defaults as oscar_defaults  # noqa: E402

OSCAR_DASHBOARD_NAVIGATION = copy.deepcopy(oscar_defaults.OSCAR_DASHBOARD_NAVIGATION)
OSCAR_DASHBOARD_NAVIGATION[3]["children"].append(
    {"label": "Announcements", "url_name": "dashboard:announcement-list"}
)

# To add a "verified" audience, register it in example_site/apps.py DashboardConfig.ready()
