"""Management command: delete expired announcements and optionally schedule daily runs."""

from django.core.management.base import BaseCommand

from oscar_announcements.models import Announcement


class Command(BaseCommand):
    help = "Delete all announcements whose publish_end has passed."

    def handle(self, *args, **options):
        count, _ = Announcement.delete_expired_announcements()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {count} expired announcement(s).")
        )
