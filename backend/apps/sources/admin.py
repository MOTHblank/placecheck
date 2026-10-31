from django.contrib import admin

from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "is_active", "rate_limit_per_minute", "created_at")
    list_filter = ("provider_type", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
