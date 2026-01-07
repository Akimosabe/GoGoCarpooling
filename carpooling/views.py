from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Trip, Booking
from .serializers import TripSerializer, BookingSerializer, UserSerializer
from django.contrib.auth.models import User

# ---- Аутентификация ----

@api_view(['POST'])
def register(request):
    # Логика регистрации пользователя
    # Нужно добавить создание пользователя и хеширование пароля
    pass

@api_view(['POST'])
def login(request):
    # Логика входа пользователя
    # Нужно добавить логику аутентификации
    pass

@api_view(['POST'])
def logout(request):
    # Логика выхода пользователя
    # Необходимо завершить сессию пользователя
    pass

@api_view(['GET'])
def current_user(request):
    # Логика получения текущего пользователя
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    return Response({"message": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


# ---- Поездки (Trips) ----

@api_view(['GET'])
def trip_list(request):
    # Логика для получения списка активных поездок
    trips = Trip.objects.filter(status="active")
    serializer = TripSerializer(trips, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def trip_detail(request, trip_id):
    # Логика для получения информации по конкретной поездке
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TripSerializer(trip)
    return Response(serializer.data)

@api_view(['POST'])
def create_trip(request):
    # Логика для создания новой поездки
    serializer = TripSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def edit_trip(request, trip_id):
    # Логика для редактирования существующей поездки
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = TripSerializer(trip, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def cancel_trip(request, trip_id):
    # Логика для отмены поездки
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)

    trip.status = 'cancelled'
    trip.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---- Бронирования (Bookings) ----

@api_view(['POST'])
def book_seat(request, trip_id):
    # Логика для бронирования места на поездке
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = BookingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(trip=trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def cancel_booking(request, booking_id):
    # Логика для отмены бронирования (пассажир или водитель)
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({"message": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

    booking.status = 'cancelled'
    booking.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def user_bookings(request):
    # Логика для получения всех бронирований пользователя
    if not request.user.is_authenticated:
        return Response({"message": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    bookings = Booking.objects.filter(passenger_id=request.user.id)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def trip_bookings(request, trip_id):
    # Логика для получения всех бронирований на конкретной поездке (для водителя)
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)

    bookings = Booking.objects.filter(trip=trip)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)


# ---- Пинг (Ping) ----
# Представление для тестирования работоспособности API

@api_view(['GET'])
def ping(request):
    return Response({"status": "ok", "message": "DRF is working"}, status=status.HTTP_200_OK)
