from django.contrib import admin

from .models import SyncRun


@admin.register(SyncRun)
class SyncRunAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "status", "is_complete", "processed_count", "deactivated_count", "failure", "started_at", "finished_at")
    list_filter = ("source", "status", "is_complete")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
