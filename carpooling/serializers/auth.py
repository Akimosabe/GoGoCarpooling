from rest_framework import serializers
from django.contrib.auth.models import User
from carpooling.models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    # Обязательные поля профиля
    phone = serializers.CharField(required=True, min_length=10, max_length=20)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value
    
    def validate_phone(self, value):
        """Валидация номера телефона (российский формат)"""
        import re
        # Убираем все символы кроме цифр и +
        phone_clean = re.sub(r'[^\d+]', '', value)
        
        # Проверяем российские форматы: +7XXXXXXXXXX, 8XXXXXXXXXX, 7XXXXXXXXXX
        if not re.match(r'^(\+7|8|7)\d{10}$', phone_clean):
            raise serializers.ValidationError(
                "Неверный формат телефона. Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
        
        # Проверка уникальности телефона
        if UserProfile.objects.filter(phone=phone_clean).exists():
            raise serializers.ValidationError("Пользователь с таким номером телефона уже зарегистрирован")
        
        return phone_clean
    
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
