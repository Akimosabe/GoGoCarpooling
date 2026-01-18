from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from carpooling.models import User
from carpooling.tasks import send_password_reset_email
from carpooling.serializers import (
    RegisterSerializer, LoginSerializer,
    UserSerializer, UserDetailSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Регистрация нового пользователя"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "Пользователь успешно зарегистрирован",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Вход пользователя"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Аутентификация по email
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            return Response({
                "message": "Успешный вход",
                "user": UserDetailSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Неверный email или пароль"
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Выход пользователя"""
    auth_logout(request)
    return Response({"message": "Успешный выход"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Получение информации о текущем пользователе"""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Запрос на восстановление пароля"""
    email = request.data.get('email')
    
    if not email:
        return Response(
            {"message": "Email обязателен"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Не раскрываем, существует ли пользователь
        return Response({
            "message": "Если пользователь с таким email существует, на него отправлена ссылка для восстановления пароля"
        })
    
    # Генерация токена
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Формирование ссылки для восстановления (для фронтенда)
    reset_link = f"http://localhost:3000/password-reset/{uid}/{token}/"
    
    # Асинхронная отправка email через Celery
    send_password_reset_email.delay(
        user_email=user.email,
        user_name=user.first_name or user.email,
        reset_link=reset_link
    )
    
    return Response({
        "message": "Если пользователь с таким email существует, на него отправлена ссылка для восстановления пароля"
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, uidb64, token):
    """Подтверждение восстановления пароля и установка нового"""
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')
    
    if not new_password or not new_password_confirm:
        return Response(
            {"message": "Оба поля пароля обязательны"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != new_password_confirm:
        return Response(
            {"message": "Пароли не совпадают"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {"message": "Пароль должен содержать минимум 8 символов"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"message": "Неверная ссылка восстановления"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not default_token_generator.check_token(user, token):
        return Response(
            {"message": "Ссылка восстановления недействительна или истекла"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.set_password(new_password)
    user.save(update_fields=['password'])
    
    return Response({"message": "Пароль успешно изменен"})
