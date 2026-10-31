from django.contrib import admin

from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "is_active", "is_published", "can_store_description", "can_retain_price_history", "can_retain_analytics", "rate_limit_per_minute", "created_at")
    list_filter = ("provider_type", "is_active", "is_published")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
