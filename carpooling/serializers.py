from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Trip, Booking, UserProfile, Car, Rating, Notification, City


# ============ Сериализаторы для пользователей ============

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
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'phone', 'bio', 'avatar', 'date_of_birth',
            'trips_as_driver', 'trips_as_passenger', 
            'average_rating', 'total_ratings_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'trips_as_driver', 'trips_as_passenger', 'created_at', 'updated_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор пользователя с профилем и машинами"""
    profile = UserProfileSerializer(read_only=True)
    cars = CarSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'cars']


# ============ Сериализаторы для поездок ============

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


# ============ Сериализаторы для бронирований ============

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


# ============ Сериализаторы для рейтингов ============

class RatingSerializer(serializers.ModelSerializer):
    """Сериализатор для рейтингов"""
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'trip', 'from_user', 'to_user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'from_user', 'created_at']


class RatingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рейтинга"""
    
    class Meta:
        model = Rating
        fields = ['trip', 'to_user', 'rating', 'comment']
    
    def validate_rating(self, value):
        """Проверка значения рейтинга"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 5")
        return value


# ============ Сериализаторы для уведомлений ============

class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор для уведомлений"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'trip', 'booking', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============ Сериализаторы для аутентификации ============

class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    
    # Дополнительные поля профиля
    phone = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone']
    
    def validate(self, data):
        """Проверка совпадения паролей"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return data
    
    def create(self, validated_data):
        """Создание пользователя с профилем"""
        validated_data.pop('password_confirm')
        phone = validated_data.pop('phone', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        
        # Создание профиля
        UserProfile.objects.create(user=user, phone=phone)
        
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
