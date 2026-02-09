from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone

from carpooling.models import Trip, Booking, User, Notification
from carpooling.serializers import (
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer
)
from carpooling.pagination import paginate_queryset
from .utils import create_notification


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_seat(request, trip_id):
    """Бронирование места в поездке"""
    try:
        trip = Trip.objects.select_related('origin', 'destination').get(id=trip_id)
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
    
    # Ранее отменённое или отклонённое бронирование — повторное бронирование запрещено
    previous_booking = Booking.objects.filter(
        trip=trip, passenger=request.user
    ).exclude(
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
    ).first()
    if previous_booking:
        if previous_booking.status == Booking.STATUS_CANCELLED:
            return Response({
                "message": "Вы уже бронировались в эту поездку. Ваше бронирование было отменено.",
                "code": "previous_booking_cancelled",
            }, status=status.HTTP_400_BAD_REQUEST)
        if previous_booking.status == Booking.STATUS_REJECTED:
            return Response({
                "message": "Вы уже бронировались в эту поездку. Ваше бронирование было отклонено водителем.",
                "code": "previous_booking_rejected",
            }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = BookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    seats_count = serializer.validated_data['seats_count']
    
    # Создание бронирования с блокировкой: проверка дубликата и мест внутри транзакции
    try:
        with transaction.atomic():
            trip = Trip.objects.select_for_update().select_related(
                'origin', 'destination'
            ).get(id=trip_id)
            
            if Booking.objects.filter(
                trip=trip,
                passenger=request.user,
                status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
            ).exists():
                return Response({
                    "message": "У вас уже есть бронирование на эту поездку"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if trip.available_seats < seats_count:
                return Response({
                    "message": f"Недостаточно свободных мест. Доступно: {trip.available_seats}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            booking = serializer.save(
                trip=trip,
                passenger=request.user,
                status=Booking.STATUS_CONFIRMED
            )
            
            # Уменьшаем доступные места
            trip.available_seats -= seats_count
            trip.save()
            
            # Уведомляем водителя о новом бронировании
            create_notification(
                user=trip.driver,
                notification_type=Notification.TYPE_BOOKING_NEW,
                title="Новое бронирование",
                message=f"{request.user.first_name or request.user.email} забронировал {seats_count} мест в поездке {trip.origin.name} → {trip.destination.name}",
                trip=trip,
                booking=booking
            )
        
        return Response(BookingDetailSerializer(booking).data, status=status.HTTP_201_CREATED)
    except IntegrityError:
        previous_booking = Booking.objects.filter(
            trip_id=trip_id, passenger=request.user
        ).first()
        if previous_booking and previous_booking.status == Booking.STATUS_REJECTED:
            return Response({
                "message": "Вы уже бронировались в эту поездку. Ваше бронирование было отклонено водителем.",
                "code": "previous_booking_rejected",
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "Вы уже бронировались в эту поездку. Ваше бронирование было отменено.",
            "code": "previous_booking_cancelled",
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """Отмена бронирования пассажиром"""
    try:
        booking = Booking.objects.select_related('trip', 'trip__origin', 'trip__destination').get(
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
            message=f"{request.user.first_name or request.user.email} отменил бронирование в поездке {booking.trip.origin.name} → {booking.trip.destination.name}",
            trip=booking.trip,
            booking=booking
        )
    
    return Response({"message": "Бронирование успешно отменено"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_booking(request, booking_id):
    """Отклонение бронирования водителем"""
    try:
        booking = Booking.objects.select_related('trip', 'trip__origin', 'trip__destination').get(id=booking_id)
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
            message=f"Ваше бронирование в поездке {booking.trip.origin.name} → {booking.trip.destination.name} было отклонено водителем",
            trip=booking.trip,
            booking=booking
        )
    
    return Response({"message": "Бронирование отклонено"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookings(request):
    """Бронирования текущего пользователя. ?archive=1 — только архив. Сортировка по дате поездки: новые сверху."""
    now = timezone.now()
    bookings = Booking.objects.filter(
        passenger=request.user
    ).select_related('trip', 'trip__driver', 'trip__origin', 'trip__destination')
    archive = request.query_params.get('archive', '').lower() in ('1', 'true', 'yes')
    if archive:
        bookings = bookings.filter(
            Q(trip__status__in=[Trip.STATUS_CANCELLED, Trip.STATUS_COMPLETED]) |
            Q(trip__status=Trip.STATUS_ACTIVE, trip__departure_datetime__lt=now)
        )
        bookings = bookings.order_by('-trip__departure_datetime')
    else:
        bookings = bookings.filter(
            trip__status=Trip.STATUS_ACTIVE,
            trip__departure_datetime__gte=now
        )
        bookings = bookings.order_by('trip__departure_datetime')
    return paginate_queryset(request, bookings, BookingListSerializer)


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
    return paginate_queryset(request, bookings, BookingListSerializer)
