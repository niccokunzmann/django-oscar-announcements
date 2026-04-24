from oscar.apps.dashboard.apps import DashboardConfig as OscarDashboardConfig


class DashboardConfig(OscarDashboardConfig):
    def configure_permissions(self):
        super().configure_permissions()
        from oscar_announcements.dashboard.urls import permissions as ann_permissions
        self.permissions_map.update(ann_permissions)

    def get_urls(self):
        from oscar_announcements.dashboard.urls import urlpatterns as ann_urls

        urls = super().get_urls()
        urls += self.post_process_urls(ann_urls)
        return urls
