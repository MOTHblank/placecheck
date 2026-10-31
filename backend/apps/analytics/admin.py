from django.contrib import admin

from .models import RedirectEvent


@admin.register(RedirectEvent)
class RedirectEventAdmin(admin.ModelAdmin):
    list_display = ("listing_key", "source_name", "exposure", "created_at")
    list_filter = ("created_at",)
    search_fields = ("source_slug",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
