from rest_framework import serializers
from django.contrib.auth.models import User
from carpooling.models import UserProfile, Car, Booking, Trip


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CarSerializer(serializers.ModelSerializer):
    """Сериализатор для автомобиля"""
    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'year', 'color', 'license_plate', 'is_active']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя"""
    user = UserSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_ratings_count = serializers.ReadOnlyField()
    phone = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'phone', 'bio', 'avatar', 'date_of_birth',
            'trips_as_driver', 'trips_as_passenger', 
            'average_rating', 'total_ratings_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'trips_as_driver', 'trips_as_passenger', 'created_at', 'updated_at']
    
    def get_phone(self, obj):
        """Показываем телефон только владельцу, водителю поездки или забронированному пассажиру"""
        request = self.context.get('request')
        
        # Если нет request или пользователь не авторизован
        if not request or not request.user.is_authenticated:
            return None
        
        # Показываем владельцу профиля
        if obj.user == request.user:
            return obj.phone
        
        # Проверяем, есть ли общие поездки
        
        # Если запрашивающий - водитель, а владелец профиля - его пассажир
        driver_trips = Trip.objects.filter(
            driver=request.user,
            bookings__passenger=obj.user,
            bookings__status=Booking.STATUS_CONFIRMED
        ).exists()
        
        # Если запрашивающий - пассажир, а владелец профиля - водитель его поездки
        passenger_trips = Trip.objects.filter(
            driver=obj.user,
            bookings__passenger=request.user,
            bookings__status=Booking.STATUS_CONFIRMED
        ).exists()
        
        if driver_trips or passenger_trips:
            return obj.phone
        
        return None


class UserDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор пользователя с профилем и машинами"""
    profile = UserProfileSerializer(read_only=True)
    cars = CarSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'cars']
