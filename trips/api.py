from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Trip
from .serializers import TripSerializer
from django.shortcuts import get_object_or_404


# тестовый пинг
class PingAPIView(APIView):
    def get(self, request):
        return Response({"status": "ok", "message": "DRF is working"})


# по статусу
class TripListAPIView(APIView):
    def get(self, request):
        trips = Trip.objects.filter(status="active")
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)


# по ид
class TripDetailAPIView(APIView):
    def get(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk, status="active")
        serializer = TripSerializer(trip)
        return Response(serializer.data)
