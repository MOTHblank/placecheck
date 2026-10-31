from django.db import models


class MatchDecision(models.Model):
    listing = models.ForeignKey("listings.Listing", on_delete=models.CASCADE, related_name="match_decisions")
    candidate = models.ForeignKey("listings.Listing", null=True, on_delete=models.SET_NULL, related_name="candidate_decisions")
    previous_property = models.ForeignKey("properties.Property", null=True, on_delete=models.SET_NULL, related_name="departing_decisions")
    assigned_property = models.ForeignKey("properties.Property", on_delete=models.PROTECT, related_name="match_decisions")
    outcome = models.CharField(max_length=20, choices=[("automatic", "Automatic"), ("possible", "Possible"), ("separate", "Separate")])
    score = models.FloatField(default=0)
    reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
