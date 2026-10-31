from django.db.models import Count, Min, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, pagination
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.http import HttpResponseRedirect

from apps.analytics.models import RedirectEvent
from apps.listings.models import Listing

from .filters import filter_properties, ordering_expression
from .models import Property
from .serializers import PropertyDetailSerializer, PropertyListSerializer


class PropertyPagination(pagination.LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class PropertyListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PropertyListSerializer
    pagination_class = PropertyPagination

    def get_queryset(self):
        active_listings = Q(listings__is_active=True)
        queryset = Property.objects.filter(active_listings).annotate(
            listing_count=Count("listings", filter=active_listings, distinct=True),
            min_price=Min("listings__price", filter=active_listings),
        ).distinct()
        queryset = filter_properties(queryset, self.request.query_params)
        return queryset.order_by(ordering_expression(self.request.query_params.get("ordering", "-updated_at")))


class PropertyDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PropertyDetailSerializer

    def get_queryset(self):
        active_listings = Q(listings__is_active=True)
        return Property.objects.filter(active_listings).annotate(
            listing_count=Count("listings", filter=active_listings, distinct=True),
            min_price=Min("listings__price", filter=active_listings),
        ).distinct()


class ListingRedirectView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, listing_id):
        listing = get_object_or_404(Listing.objects.select_related("property"), pk=listing_id, is_active=True)
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
