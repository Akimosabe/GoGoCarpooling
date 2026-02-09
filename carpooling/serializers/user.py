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
    """Сериализатор профиля пользователя (полный). phone — редактируемое поле при обновлении своего профиля."""
    average_rating = serializers.ReadOnlyField()
    total_ratings_count = serializers.ReadOnlyField()
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
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
