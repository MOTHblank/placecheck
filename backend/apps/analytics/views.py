from rest_framework import generics, serializers
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import accept_event
from .schema import EventSchema


class EventInput(serializers.Serializer):
    event_id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=["search", "view", "exposure"])
    receipt = serializers.CharField(required=False, max_length=32768)
    context = serializers.CharField(required=False, max_length=32768)
    listing_id = serializers.IntegerField(required=False, min_value=1)


class EventView(generics.GenericAPIView):
    schema = EventSchema()
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    serializer_class = EventInput

    def post(self, request):
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        result, created = accept_event(request, payload.validated_data)
        response = Response(result, status=201 if created else 200 if result["accepted"] else 202)
        response["Cache-Control"] = "private, no-store"
        return response
