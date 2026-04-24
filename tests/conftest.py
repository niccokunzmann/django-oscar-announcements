"""Minimal Django settings for the package test suite."""

import django
from pathlib import Path
from django.conf import settings

TESTS_DIR = Path(__file__).parent


def pytest_configure():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.sessions",
                "django.contrib.messages",
                "pinax.announcements",
                "oscar_announcements",
            ],
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            USE_TZ=True,
            SECRET_KEY="test-secret-key-not-for-production",
            STATIC_URL="/static/",
            ROOT_URLCONF="tests.urls",
            MIDDLEWARE=[
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
            ],
            SESSION_ENGINE="django.contrib.sessions.backends.db",
            MESSAGE_STORAGE="django.contrib.messages.storage.cookie.CookieStorage",
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [TESTS_DIR / "templates"],
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.request",
                            "django.contrib.messages.context_processors.messages",
                        ]
                    },
                }
            ],
        )
        django.setup()
