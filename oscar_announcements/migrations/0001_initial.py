from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("announcements", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Announcement",
            fields=[
                (
                    "announcement_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="announcements.announcement",
                    ),
                ),
                (
                    "level",
                    models.CharField(
                        choices=[("info", "Info"), ("warning", "Warning")],
                        default="info",
                        max_length=10,
                        verbose_name="level",
                    ),
                ),
                (
                    "visibility",
                    models.CharField(
                        default="registered",
                        help_text="Which audience can see this announcement.",
                        max_length=50,
                        verbose_name="visibility",
                    ),
                ),
            ],
            options={
                "verbose_name": "announcement",
                "verbose_name_plural": "announcements",
            },
            bases=("announcements.announcement",),
        ),
    ]
