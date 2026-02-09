from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from carpooling.models import Trip, User, Notification
from carpooling.serializers import (
    TripListSerializer, TripDetailSerializer, TripCreateUpdateSerializer
)
from carpooling.pagination import paginate_queryset
from .utils import create_notification


@api_view(['GET'])
@permission_classes([AllowAny])
def trip_list(request):
    """Получение списка активных поездок с фильтрацией"""
    # Фильтруем только активные поездки с датой в будущем
    trips = Trip.objects.filter(
        status=Trip.STATUS_ACTIVE,
        departure_datetime__gte=timezone.now()
    ).select_related('driver', 'car', 'origin', 'destination')
    
    # Фильтры
    origin = request.query_params.get('origin')  # Название города или ID
    origin_id = request.query_params.get('origin_id')  # ID города
    destination = request.query_params.get('destination')  # Название города или ID
    destination_id = request.query_params.get('destination_id')  # ID города
    date = request.query_params.get('date')
    min_seats = request.query_params.get('min_seats')
    max_price = request.query_params.get('max_price')
    
    # Фильтрация по городу отправления
    if origin_id:
        try:
            trips = trips.filter(origin_id=int(origin_id))
        except ValueError:
            pass
    elif origin:
        trips = trips.filter(origin__name__icontains=origin)
    
    # Фильтрация по городу назначения
    if destination_id:
        try:
            trips = trips.filter(destination_id=int(destination_id))
        except ValueError:
            pass
    elif destination:
        trips = trips.filter(destination__name__icontains=destination)
    
    if date:
        try:
            # Поддержка обоих форматов даты
            for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
                try:
                    date_obj = datetime.strptime(date, fmt).date()
                    trips = trips.filter(departure_datetime__date=date_obj)
                    break
                except ValueError:
                    continue
        except Exception:
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
    
    return paginate_queryset(request, trips, TripListSerializer)


@api_view(['GET'])
@permission_classes([AllowAny])
def trip_detail(request, trip_id):
    """Получение детальной информации о поездке"""
    try:
        trip = Trip.objects.select_related('driver', 'car', 'origin', 'destination').get(id=trip_id)
        serializer = TripDetailSerializer(trip, context={'request': request})
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
        return Response(TripDetailSerializer(trip, context={'request': request}).data, status=status.HTTP_201_CREATED)
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
        from carpooling.models import Booking
        bookings = trip.bookings.filter(status=Booking.STATUS_CONFIRMED)
        for booking in bookings:
            create_notification(
                user=booking.passenger,
                notification_type=Notification.TYPE_TRIP_UPDATED,
                title="Поездка обновлена",
                message=f"Поездка {trip.origin.name} → {trip.destination.name} была обновлена",
                trip=trip
            )
        
        return Response(TripDetailSerializer(trip, context={'request': request}).data)
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
        from carpooling.models import Booking
        bookings = trip.bookings.filter(status=Booking.STATUS_CONFIRMED)
        for booking in bookings:
            booking.status = Booking.STATUS_CANCELLED
            booking.save()
            
            create_notification(
                user=booking.passenger,
                notification_type=Notification.TYPE_TRIP_CANCELLED,
                title="Поездка отменена",
                message=f"Поездка {trip.origin.name} → {trip.destination.name} была отменена водителем",
                trip=trip,
                booking=booking
            )
    
    return Response({"message": "Поездка успешно отменена"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_trips(request):
    """Получение поездок текущего пользователя как водителя"""
    trips = Trip.objects.filter(driver=request.user).select_related('car', 'origin', 'destination')
    
    # Автоматически завершаем просроченные поездки
    for trip in trips:
        trip.check_and_complete_if_expired()
    
    # Перезагружаем после возможных изменений и сортируем
    trips = Trip.objects.filter(driver=request.user).select_related(
        'car', 'origin', 'destination'
    ).order_by('-departure_datetime')
    
    return paginate_queryset(request, trips, TripListSerializer)
