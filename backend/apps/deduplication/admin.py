from django.contrib import admin
from .models import MatchDecision


@admin.register(MatchDecision)
class MatchDecisionAdmin(admin.ModelAdmin):
    list_display = ("listing", "candidate", "outcome", "score", "previous_property", "assigned_property", "created_at")
    list_filter = ("outcome",)
    readonly_fields = ("listing", "candidate", "outcome", "score", "reasons", "previous_property", "assigned_property", "created_at")

    def has_add_permission(self, request):
        return False
