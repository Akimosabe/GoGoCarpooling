from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from carpooling.models import Trip, Booking, UserProfile, Notification
from carpooling.serializers import (
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer
)
from .utils import create_notification


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
