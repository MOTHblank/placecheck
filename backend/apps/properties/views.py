from django.shortcuts import get_object_or_404
from rest_framework import generics, pagination
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseRedirect

from apps.analytics.services import receipt, record_redirect
from apps.listings.models import Listing

from .filters import SearchParameters
from .selectors import matching_offers, property_search
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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["analytics_receipt"] = receipt(request, "search", self.search_params,
                                                   offers=matching_offers(self.search_params))
        response["Cache-Control"] = "private, no-store"
        return response

    def get_queryset(self):
        params = SearchParameters(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        self.search_params = params.validated_data
        return property_search(params.validated_data)


class PropertyDetailView(generics.RetrieveAPIView):
    schema = PropertySchema()
    permission_classes = [AllowAny]
    serializer_class = PropertyDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        property_ = self.get_object()
        response = Response(self.get_serializer(property_).data)
        response.data["analytics_receipt"] = receipt(request, "view", self.search_params,
            offers=matching_offers(self.search_params).filter(property_id=property_.pk,
                pk__in=[offer["id"] for offer in response.data["listings"]]), property_=property_)
        response["Cache-Control"] = "private, no-store"
        return response

    def get_queryset(self):
        params = SearchParameters(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        self.search_params = params.validated_data
        return property_search(params.validated_data, include_offers=True)


class ListingRedirectView(APIView):
    schema = RedirectSchema()
    permission_classes = [AllowAny]

    def get(self, request, listing_id):
        listing = get_object_or_404(Listing.objects.select_related("property", "source"), pk=listing_id, is_active=True, source__is_published=True)
        listing = record_redirect(request, listing)
        response = HttpResponseRedirect(listing.url)
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response
