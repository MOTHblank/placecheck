from django.contrib import admin
from django.db import transaction
from apps.sources.models import Source

from .models import Listing, ListingPriceHistory


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "transaction_type", "price", "city", "is_active")
    list_filter = ("transaction_type", "is_active", "source", "state")
    search_fields = ("title", "external_id", "city", "neighborhood")
    autocomplete_fields = ("source", "property")

    def get_readonly_fields(self, request, obj=None):
        return ("price", "source", "external_id", "sale_method", "price_kind", "source_inventory_date") if obj else ()

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        obj.source = Source.objects.select_for_update().get(pk=obj.source_id)
        if not obj.source.can_store_description:
            obj.description = ""
        super().save_model(request, obj, form, change)
        if not change and obj.source.can_retain_price_history and obj.price is not None:
            ListingPriceHistory.objects.create(listing=obj, price=obj.price)


@admin.register(ListingPriceHistory)
class ListingPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("listing", "price", "captured_at")
    list_filter = ("captured_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
