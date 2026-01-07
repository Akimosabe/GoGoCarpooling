from rest_framework import serializers
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    driver = serializers.StringRelatedField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "driver",
            "origin",
            "destination",
            "departure_datetime",
            "price",
            "total_seats",
            "available_seats",
            "status",
        ]
