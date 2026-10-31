from django.shortcuts import get_object_or_404
from rest_framework import generics, pagination
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.http import HttpResponseRedirect

from apps.analytics.models import RedirectEvent
from apps.listings.models import Listing

from .filters import SearchParameters
from .selectors import property_search
from .serializers import PropertyDetailSerializer, PropertyListSerializer
from .schema import PropertySchema, RedirectSchema


class PropertyPagination(pagination.LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class PropertyListView(generics.ListAPIView):
    schema = PropertySchema()
    permission_classes = [AllowAny]
    serializer_class = PropertyListSerializer
    pagination_class = PropertyPagination

    def get_queryset(self):
        params = SearchParameters(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        return property_search(params.validated_data)


class PropertyDetailView(generics.RetrieveAPIView):
    schema = PropertySchema()
    permission_classes = [AllowAny]
    serializer_class = PropertyDetailSerializer

    def get_queryset(self):
        params = SearchParameters(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        return property_search(params.validated_data, include_offers=True)


class ListingRedirectView(APIView):
    schema = RedirectSchema()
    permission_classes = [AllowAny]

    def get(self, request, listing_id):
        listing = get_object_or_404(Listing.objects.select_related("property"), pk=listing_id, is_active=True, source__is_published=True)
        if not request.session.session_key:
            request.session.create()
        RedirectEvent.objects.create(
            listing=listing,
            property=listing.property,
            session_id=request.session.session_key or "",
            referer=request.META.get("HTTP_REFERER", "")[:200],
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return HttpResponseRedirect(listing.url)
