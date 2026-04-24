"""Management command: delete expired announcements and optionally schedule daily runs."""

from django.core.management.base import BaseCommand

from oscar_announcements.tasks import delete_expired_announcements, schedule_daily_cleanup


class Command(BaseCommand):
    help = "Delete all announcements whose publish_end has passed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--schedule",
            action="store_true",
            help="Also queue a daily background task to run this automatically.",
        )

    def handle(self, *args, **options):
        count, _ = delete_expired_announcements()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired announcement(s)."))

        if options["schedule"]:
            schedule_daily_cleanup()
            self.stdout.write("Daily cleanup scheduled.")
