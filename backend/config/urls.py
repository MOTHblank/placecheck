from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.urls import include
from rest_framework.schemas import get_schema_view
from rest_framework.permissions import AllowAny

from apps.properties.views import ListingRedirectView


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/", include("apps.properties.urls")),
    path("out/<int:listing_id>/", ListingRedirectView.as_view(), name="listing-redirect"),
    path(
        "api/schema/",
        get_schema_view(
            title="Placecheck API",
            description="API de busca e comparação de imóveis.",
            version="1.0.0",
            public=True,
            permission_classes=[AllowAny],
        ),
        name="openapi-schema",
    ),
]
