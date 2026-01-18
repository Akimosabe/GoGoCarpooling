from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from carpooling.models import User, Car
from carpooling.serializers import (
    UserDetailSerializer, UserProfileSerializer, CarSerializer
)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile(request, user_id):
    """Получение профиля пользователя"""
    try:
        user = User.objects.get(id=user_id)
        serializer = UserDetailSerializer(user, context={'request': request})
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Обновление профиля текущего пользователя"""
    serializer = UserProfileSerializer(
        request.user, 
        data=request.data, 
        partial=True,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def car_list_create(request):
    """Получение списка машин пользователя или создание новой"""
    if request.method == 'GET':
        cars = request.user.cars.all()
        serializer = CarSerializer(cars, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def car_detail(request, car_id):
    """Обновление или удаление машины"""
    try:
        car = Car.objects.get(id=car_id, owner=request.user)
    except Car.DoesNotExist:
        return Response({"message": "Автомобиль не найден"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        serializer = CarSerializer(car, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        car.delete()
        return Response({"message": "Автомобиль удален"}, status=status.HTTP_204_NO_CONTENT)
