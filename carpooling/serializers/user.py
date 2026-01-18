from rest_framework import serializers
from carpooling.models import User, Car, Booking, Trip


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'avatar']


class CarSerializer(serializers.ModelSerializer):
    """Сериализатор для автомобиля"""
    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'year', 'color', 'license_plate', 'is_active']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя (полный)"""
    average_rating = serializers.ReadOnlyField()
    total_ratings_count = serializers.ReadOnlyField()
    phone = serializers.SerializerMethodField()
    cars = CarSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'phone', 'avatar', 'date_of_birth',
            'trips_as_driver', 'trips_as_passenger', 
            'average_rating', 'total_ratings_count',
            'cars', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'trips_as_driver', 'trips_as_passenger', 
            'created_at', 'updated_at'
        ]
    
    def get_phone(self, obj):
        """Показываем телефон только владельцу, водителю поездки или забронированному пассажиру"""
        request = self.context.get('request')
        
        # Если нет request или пользователь не авторизован
        if not request or not request.user.is_authenticated:
            return None
        
        # Показываем владельцу профиля
        if obj == request.user:
            return obj.phone
        
        # Проверяем, есть ли общие поездки
        
        # Если запрашивающий - водитель, а владелец профиля - его пассажир
        driver_trips = Trip.objects.filter(
            driver=request.user,
            bookings__passenger=obj,
            bookings__status=Booking.STATUS_CONFIRMED
        ).exists()
        
        # Если запрашивающий - пассажир, а владелец профиля - водитель его поездки
        passenger_trips = Trip.objects.filter(
            driver=obj,
            bookings__passenger=request.user,
            bookings__status=Booking.STATUS_CONFIRMED
        ).exists()
        
        if driver_trips or passenger_trips:
            return obj.phone
        
        return None


class UserDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор пользователя с машинами"""
    average_rating = serializers.ReadOnlyField()
    total_ratings_count = serializers.ReadOnlyField()
    cars = CarSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'phone', 'avatar', 'date_of_birth',
            'trips_as_driver', 'trips_as_passenger',
            'average_rating', 'total_ratings_count',
            'cars', 'is_staff', 'is_superuser', 'created_at'
        ]
