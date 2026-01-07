from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Trip, Booking

# Сериализатор для пользователя (аутентификация)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']  # Можно добавить больше полей при необходимости

# Сериализатор для поездки
class TripSerializer(serializers.ModelSerializer):
    driver = serializers.StringRelatedField()  # Можно заменить на DriverSerializer для более подробной информации
    status = serializers.ChoiceField(choices=Trip.STATUS_CHOICES)  # Если статус является выбором
    departure_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # Форматируем дату для удобства

    class Meta:
        model = Trip
        fields = '__all__'  # Если нужно сериализовать все поля
        # или можно явным образом перечислить нужные поля:
        # fields = ["id", "driver", "origin", "destination", "departure_datetime", "price", "total_seats", "available_seats", "status"]

# Сериализатор для бронирования
class BookingSerializer(serializers.ModelSerializer):
    passenger = UserSerializer()  # Сериализуем данные пассажира через UserSerializer
    trip = TripSerializer()  # Сериализуем данные поездки

    class Meta:
        model = Booking
        fields = ['id', 'trip', 'passenger', 'status', 'created_at']  # Создаём все необходимые поля
        # 'created_at' для отслеживания времени создания бронирования

# Сериализатор для регистрации (включая поле для пароля)
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Пароль только для записи

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        # Создаём пользователя с хешированным паролем
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user

# Сериализатор для входа (проверка пароля)
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
