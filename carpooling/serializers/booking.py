from rest_framework import serializers
from carpooling.models import Booking
from .user import UserSerializer, UserDetailSerializer
from .trip import TripListSerializer, TripDetailSerializer


class BookingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка бронирований"""
    passenger = UserSerializer(read_only=True)
    trip = TripListSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'trip', 'passenger', 'seats_count', 
            'status', 'comment', 'created_at'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор бронирования"""
    passenger = UserDetailSerializer(read_only=True)
    trip = TripDetailSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'trip', 'passenger', 'seats_count',
            'status', 'comment', 'rejection_reason',
            'created_at', 'updated_at'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бронирования"""
    
    class Meta:
        model = Booking
        fields = ['seats_count', 'comment']
    
    def validate_seats_count(self, value):
        """Проверка количества мест"""
        if value < 1:
            raise serializers.ValidationError("Необходимо забронировать хотя бы одно место")
        return value
