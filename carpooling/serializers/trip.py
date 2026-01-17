from rest_framework import serializers
from carpooling.models import Trip, City, Booking
from .user import UserSerializer, UserDetailSerializer, CarSerializer


class CitySerializer(serializers.ModelSerializer):
    """Сериализатор для городов"""
    class Meta:
        model = City
        fields = ['id', 'name', 'region', 'country', 'is_popular']


class TripListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка поездок (упрощенный)"""
    driver = UserSerializer(read_only=True)
    driver_rating = serializers.SerializerMethodField()
    car = CarSerializer(read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'driver', 'driver_rating', 'car',
            'origin', 'destination', 'departure_datetime',
            'price', 'total_seats', 'available_seats',
            'smoking_allowed', 'pets_allowed', 'luggage_size',
            'status', 'created_at'
        ]
    
    def get_driver_rating(self, obj):
        """Получить рейтинг водителя"""
        if hasattr(obj.driver, 'profile'):
            return obj.driver.profile.average_rating
        return 0


class TripDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор поездки"""
    driver = UserDetailSerializer(read_only=True)
    car = CarSerializer(read_only=True)
    bookings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'driver', 'car',
            'origin', 'destination', 'departure_datetime',
            'price', 'total_seats', 'available_seats',
            'description', 'smoking_allowed', 'pets_allowed', 'luggage_size',
            'bookings_count', 'status', 'created_at', 'updated_at'
        ]
    
    def get_bookings_count(self, obj):
        """Количество активных бронирований"""
        return obj.bookings.filter(status=Booking.STATUS_CONFIRMED).count()


class TripCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления поездки"""
    
    class Meta:
        model = Trip
        fields = [
            'car', 'origin', 'destination', 'departure_datetime',
            'price', 'total_seats', 'available_seats',
            'description', 'smoking_allowed', 'pets_allowed', 'luggage_size'
        ]
    
    def validate_total_seats(self, value):
        """Валидация количества мест"""
        if value < 1 or value > 9:
            raise serializers.ValidationError("Количество мест должно быть от 1 до 9")
        return value
    
    def validate_available_seats(self, value):
        """Валидация доступных мест"""
        if value < 0 or value > 9:
            raise serializers.ValidationError("Количество доступных мест должно быть от 0 до 9")
        return value
    
    def validate(self, data):
        """Валидация данных поездки"""
        if 'available_seats' in data and 'total_seats' in data:
            if data['available_seats'] > data['total_seats']:
                raise serializers.ValidationError(
                    "Доступных мест не может быть больше общего количества мест"
                )
        
        if 'price' in data and data['price'] < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        
        return data
    
    def create(self, validated_data):
        """Создание поездки с автоматической установкой водителя"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['driver'] = request.user
        return super().create(validated_data)
