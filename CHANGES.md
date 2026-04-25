# Changelog

## v0.2.0

- **Anonymous visitors can now see announcements.**
  A new built-in audience *Everyone (including anonymous visitors)* targets all
  users regardless of login status.  Dismissals for anonymous users are stored
  in the session.  When the visitor logs in via Oscar, session dismissals are
  automatically promoted to permanent DB records via Oscar's `user_logged_in`
  signal — no manual integration required.

## v0.1.0

- **Announcements appear in Oscar's messages div automatically — on both the
  public site and the dashboard.**
  The package now ships overrides of `oscar/partials/alert_messages.html` and
  `oscar/dashboard/partials/alert_messages.html` that inject announcements
  directly into Oscar's `<div id="messages">` alongside flash messages.
  No manual `{% render_announcements %}` call is needed.
  Requires `oscar_announcements` to be listed **before** `oscar.config.Shop`
  in `INSTALLED_APPS`.

- **Dashboard message preview strips HTML tags.**
  The announcement list no longer shows raw HTML markup in the message column;
  it renders plain text via `striptags` before truncating.

- **Dashboard form compatible with Oscar's TinyMCE/wysiwyg.**
  The announcement form now carries `novalidate` (matching Oscar's convention)
  and explicitly calls `tinymce.triggerSave()` on submit, so the editor content
  is synced correctly before the POST.

- **Removed `django-background-tasks` dependency.**
  Expiry cleanup is handled by the `cleanup_announcements` management command.
  Run it from cron or a scheduler instead.

## v0.0.2

- Remove background task dependency

## v0.0.1

- Initial version
