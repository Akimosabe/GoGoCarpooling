from rest_framework import serializers
from carpooling.models import User
import re


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'phone', 'password', 'password_confirm']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'phone': {'required': True},
        }
    
    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value
    
    def validate_phone(self, value):
        """Валидация номера телефона (российский формат)"""
        # Убираем все символы кроме цифр и +
        phone_clean = re.sub(r'[^\d+]', '', value)
        
        # Проверяем российские форматы: +7XXXXXXXXXX, 8XXXXXXXXXX, 7XXXXXXXXXX
        if not re.match(r'^(\+7|8|7)\d{10}$', phone_clean):
            raise serializers.ValidationError(
                "Неверный формат телефона. Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
        
        # Проверка уникальности телефона
        if User.objects.filter(phone=phone_clean).exists():
            raise serializers.ValidationError("Пользователь с таким номером телефона уже зарегистрирован")
        
        return phone_clean
    
    def validate(self, data):
        """Проверка совпадения паролей"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return data
    
    def create(self, validated_data):
        """Создание пользователя"""
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            first_name=validated_data.get('first_name', ''),
            password=validated_data['password']
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
