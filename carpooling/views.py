from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from datetime import datetime

from .models import Trip, Booking, UserProfile, Car, Rating, Notification, City
from .serializers import (
    TripListSerializer, TripDetailSerializer, TripCreateUpdateSerializer,
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer,
    UserSerializer, UserDetailSerializer, UserProfileSerializer,
    CarSerializer, RatingSerializer, RatingCreateSerializer,
    NotificationSerializer, RegisterSerializer, LoginSerializer, CitySerializer
)


# ============ Утилиты ============

def create_notification(user, notification_type, title, message, trip=None, booking=None):
    """Создание уведомления"""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        trip=trip,
        booking=booking
    )


# ============ Аутентификация ============

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
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return Response({
                "message": "Успешный вход",
                "user": UserDetailSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Неверное имя пользователя или пароль"
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


# ============ Профили пользователей ============

@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile(request, user_id):
    """Получение профиля пользователя"""
    try:
        user = User.objects.get(id=user_id)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Обновление профиля текущего пользователя"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Если профиль не существует, создаем его
        profile = UserProfile.objects.create(user=request.user)
    
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
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


# ============ Города ============

@api_view(['GET'])
@permission_classes([AllowAny])
def city_list(request):
    """Получение списка городов"""
    search = request.query_params.get('search', '')
    popular_only = request.query_params.get('popular', 'false').lower() == 'true'
    
    cities = City.objects.all()
    
    if search:
        cities = cities.filter(
            Q(name__icontains=search) | Q(region__icontains=search)
        )
    
    if popular_only:
        cities = cities.filter(is_popular=True)
    
    cities = cities[:20]  # Ограничение результатов
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data)


# ============ Поездки (Trips) ============

@api_view(['GET'])
@permission_classes([AllowAny])
def trip_list(request):
    """Получение списка активных поездок с фильтрацией"""
    trips = Trip.objects.filter(status=Trip.STATUS_ACTIVE).select_related('driver', 'car')
    
    # Фильтры
    origin = request.query_params.get('origin')
    destination = request.query_params.get('destination')
    date = request.query_params.get('date')
    min_seats = request.query_params.get('min_seats')
    max_price = request.query_params.get('max_price')
    
    if origin:
        trips = trips.filter(origin__icontains=origin)
    
    if destination:
        trips = trips.filter(destination__icontains=destination)
    
    if date:
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            trips = trips.filter(departure_datetime__date=date_obj)
        except ValueError:
            pass
    
    if min_seats:
        try:
            trips = trips.filter(available_seats__gte=int(min_seats))
        except ValueError:
            pass
    
    if max_price:
        try:
            trips = trips.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Сортировка
    trips = trips.order_by('departure_datetime')
    
    serializer = TripListSerializer(trips, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def trip_detail(request, trip_id):
    """Получение детальной информации о поездке"""
    try:
        trip = Trip.objects.select_related('driver', 'car').get(id=trip_id)
        serializer = TripDetailSerializer(trip)
        return Response(serializer.data)
    except Trip.DoesNotExist:
        return Response({"message": "Поездка не найдена"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_trip(request):
    """Создание новой поездки"""
    serializer = TripCreateUpdateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        trip = serializer.save()
        
        # Увеличиваем счетчик поездок водителя
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.trips_as_driver += 1
        profile.save()
        
        return Response(TripDetailSerializer(trip).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_trip(request, trip_id):
    """Редактирование поездки (только водитель)"""
    try:
        trip = Trip.objects.get(id=trip_id, driver=request.user)
    except Trip.DoesNotExist:
        return Response({
            "message": "Поездка не найдена или вы не являетесь водителем"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Нельзя редактировать завершенную или отмененную поездку
    if trip.status in [Trip.STATUS_CANCELLED, Trip.STATUS_COMPLETED]:
        return Response({
            "message": "Нельзя редактировать завершенную или отмененную поездку"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = TripCreateUpdateSerializer(trip, data=request.data, partial=True)
    if serializer.is_valid():
        trip = serializer.save()
        
        # Уведомляем всех пассажиров об изменении
        bookings = trip.bookings.filter(status=Booking.STATUS_CONFIRMED)
        for booking in bookings:
            create_notification(
                user=booking.passenger,
                notification_type=Notification.TYPE_TRIP_UPDATED,
                title="Поездка обновлена",
                message=f"Поездка {trip.origin} → {trip.destination} была обновлена",
                trip=trip
            )
        
        return Response(TripDetailSerializer(trip).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_trip(request, trip_id):
    """Отмена поездки (только водитель)"""
    try:
        trip = Trip.objects.get(id=trip_id, driver=request.user)
    except Trip.DoesNotExist:
        return Response({
            "message": "Поездка не найдена или вы не являетесь водителем"
        }, status=status.HTTP_404_NOT_FOUND)
    
    if trip.status == Trip.STATUS_CANCELLED:
        return Response({"message": "Поездка уже отменена"}, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        trip.status = Trip.STATUS_CANCELLED
        trip.save()
        
        # Уведомляем всех пассажиров об отмене
        bookings = trip.bookings.filter(status=Booking.STATUS_CONFIRMED)
        for booking in bookings:
            booking.status = Booking.STATUS_CANCELLED
            booking.save()
            
            create_notification(
                user=booking.passenger,
                notification_type=Notification.TYPE_TRIP_CANCELLED,
                title="Поездка отменена",
                message=f"Поездка {trip.origin} → {trip.destination} была отменена водителем",
                trip=trip,
                booking=booking
            )
    
    return Response({"message": "Поездка успешно отменена"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_trips(request):
    """Получение поездок текущего пользователя как водителя"""
    trips = Trip.objects.filter(driver=request.user).select_related('car')
    serializer = TripListSerializer(trips, many=True)
    return Response(serializer.data)


# ============ Бронирования (Bookings) ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_seat(request, trip_id):
    """Бронирование места в поездке"""
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Поездка не найдена"}, status=status.HTTP_404_NOT_FOUND)
    
    # Проверки
    if trip.driver == request.user:
        return Response({
            "message": "Вы не можете забронировать место в своей поездке"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if trip.status != Trip.STATUS_ACTIVE:
        return Response({
            "message": "Эта поездка недоступна для бронирования"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Проверка существующего бронирования
    existing_booking = Booking.objects.filter(
        trip=trip, 
        passenger=request.user,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
    ).first()
    
    if existing_booking:
        return Response({
            "message": "У вас уже есть активное бронирование для этой поездки"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = BookingCreateSerializer(data=request.data)
    if serializer.is_valid():
        seats_count = serializer.validated_data['seats_count']
        
        # Проверка доступности мест
        if trip.available_seats < seats_count:
            return Response({
                "message": f"Недостаточно свободных мест. Доступно: {trip.available_seats}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создание бронирования с уменьшением количества мест
        with transaction.atomic():
            booking = serializer.save(
                trip=trip,
                passenger=request.user,
                status=Booking.STATUS_CONFIRMED
            )
            
            # Уменьшаем доступные места
            trip.available_seats -= seats_count
            trip.save()
            
            # Увеличиваем счетчик поездок пассажира
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.trips_as_passenger += 1
            profile.save()
            
            # Уведомляем водителя о новом бронировании
            create_notification(
                user=trip.driver,
                notification_type=Notification.TYPE_BOOKING_NEW,
                title="Новое бронирование",
                message=f"{request.user.get_full_name() or request.user.username} забронировал {seats_count} мест в поездке {trip.origin} → {trip.destination}",
                trip=trip,
                booking=booking
            )
        
        return Response(BookingDetailSerializer(booking).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """Отмена бронирования пассажиром"""
    try:
        booking = Booking.objects.select_related('trip').get(
            id=booking_id, 
            passenger=request.user
        )
    except Booking.DoesNotExist:
        return Response({
            "message": "Бронирование не найдено"
        }, status=status.HTTP_404_NOT_FOUND)
    
    if booking.status == Booking.STATUS_CANCELLED:
        return Response({
            "message": "Бронирование уже отменено"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # Возвращаем места в поездку
        if booking.status == Booking.STATUS_CONFIRMED:
            booking.trip.available_seats += booking.seats_count
            booking.trip.save()
        
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        
        # Уведомляем водителя об отмене
        create_notification(
            user=booking.trip.driver,
            notification_type=Notification.TYPE_BOOKING_CANCELLED,
            title="Бронирование отменено",
            message=f"{request.user.get_full_name() or request.user.username} отменил бронирование в поездке {booking.trip.origin} → {booking.trip.destination}",
            trip=booking.trip,
            booking=booking
        )
    
    return Response({"message": "Бронирование успешно отменено"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_booking(request, booking_id):
    """Отклонение бронирования водителем"""
    try:
        booking = Booking.objects.select_related('trip').get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({
            "message": "Бронирование не найдено"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Проверка прав (только водитель может отклонить)
    if booking.trip.driver != request.user:
        return Response({
            "message": "Только водитель может отклонить бронирование"
        }, status=status.HTTP_403_FORBIDDEN)
    
    if booking.status != Booking.STATUS_CONFIRMED:
        return Response({
            "message": "Можно отклонить только подтвержденное бронирование"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    rejection_reason = request.data.get('rejection_reason', '')
    
    with transaction.atomic():
        # Возвращаем места в поездку
        booking.trip.available_seats += booking.seats_count
        booking.trip.save()
        
        booking.status = Booking.STATUS_REJECTED
        booking.rejection_reason = rejection_reason
        booking.save()
        
        # Уведомляем пассажира об отклонении
        create_notification(
            user=booking.passenger,
            notification_type=Notification.TYPE_BOOKING_REJECTED,
            title="Бронирование отклонено",
            message=f"Ваше бронирование в поездке {booking.trip.origin} → {booking.trip.destination} было отклонено водителем",
            trip=booking.trip,
            booking=booking
        )
    
    return Response({"message": "Бронирование отклонено"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookings(request):
    """Получение всех бронирований текущего пользователя"""
    bookings = Booking.objects.filter(
        passenger=request.user
    ).select_related('trip', 'trip__driver').order_by('-created_at')
    
    serializer = BookingListSerializer(bookings, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trip_bookings(request, trip_id):
    """Получение всех бронирований для поездки (только водитель)"""
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"message": "Поездка не найдена"}, status=status.HTTP_404_NOT_FOUND)
    
    # Только водитель может видеть все бронирования
    if trip.driver != request.user:
        return Response({
            "message": "Только водитель может просматривать бронирования"
        }, status=status.HTTP_403_FORBIDDEN)
    
    bookings = trip.bookings.select_related('passenger').order_by('-created_at')
    serializer = BookingListSerializer(bookings, many=True)
    return Response(serializer.data)


# ============ Рейтинги ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_rating(request):
    """Создание рейтинга после поездки"""
    serializer = RatingCreateSerializer(data=request.data)
    if serializer.is_valid():
        trip = serializer.validated_data['trip']
        to_user = serializer.validated_data['to_user']
        
        # Проверка, что пользователь участвовал в поездке
        is_driver = trip.driver == request.user
        is_passenger = Booking.objects.filter(
            trip=trip,
            passenger=request.user,
            status=Booking.STATUS_CONFIRMED
        ).exists()
        
        if not (is_driver or is_passenger):
            return Response({
                "message": "Вы не участвовали в этой поездке"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Проверка, что оценивается другой участник поездки
        if to_user == request.user:
            return Response({
                "message": "Вы не можете оценить себя"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создание или обновление рейтинга
        rating, created = Rating.objects.update_or_create(
            trip=trip,
            from_user=request.user,
            to_user=to_user,
            defaults={
                'rating': serializer.validated_data['rating'],
                'comment': serializer.validated_data.get('comment', '')
            }
        )
        
        return Response(
            RatingSerializer(rating).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_ratings(request, user_id):
    """Получение всех рейтингов пользователя"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)
    
    ratings = Rating.objects.filter(to_user=user).select_related('from_user', 'trip')
    serializer = RatingSerializer(ratings, many=True)
    
    return Response({
        "average_rating": user.profile.average_rating if hasattr(user, 'profile') else 0,
        "total_count": ratings.count(),
        "ratings": serializer.data
    })


# ============ Уведомления ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    """Получение уведомлений текущего пользователя"""
    unread_only = request.query_params.get('unread', 'false').lower() == 'true'
    
    notifications = request.user.notifications.all()
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')[:50]  # Последние 50
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({"message": "Уведомление отмечено как прочитанное"})
    except Notification.DoesNotExist:
        return Response({"message": "Уведомление не найдено"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    count = request.user.notifications.filter(is_read=False).update(is_read=True)
    return Response({"message": f"Отмечено {count} уведомлений как прочитанных"})


# ============ Пинг (Ping) ============

@api_view(['GET'])
@permission_classes([AllowAny])
def ping(request):
    """Тестовый endpoint для проверки работоспособности API"""
    return Response({
        "status": "ok",
        "message": "GoGoCarpool API is working",
        "version": "1.0"
    }, status=status.HTTP_200_OK)
