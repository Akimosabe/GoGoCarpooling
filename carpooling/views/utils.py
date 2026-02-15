from django.utils import timezone

from carpooling.tasks import create_notification_task
from carpooling.serializers.trip import _departure_in_origin_tz


def create_leave_rating_notifications_for_trip(trip, is_cancelled=False):
    """
    Создаёт уведомления «оставить отзыв» участникам поездки после завершения или отмены.
    Уведомление не отправляется, если пользователь уже оставлял отзыв этому участнику сегодня.
    """
    from carpooling.models import Booking, Notification, Rating

    participants = [trip.driver]
    confirmed = trip.bookings.filter(status=Booking.STATUS_CONFIRMED).select_related('passenger')
    participants.extend(b.passenger for b in confirmed)
    today = timezone.now().date()
    route = f"{trip.origin.name} → {trip.destination.name}"
    dt_str = _trip_datetime_for_message(trip)
    route_dt = f"{route}" + (f" ({dt_str})" if dt_str else "")

    if is_cancelled:
        title = "Поездка отменена"
        msg_base = f"Поездка {route_dt} отменена. Оставьте отзыв участнику: "
    else:
        title = "Поездка завершена"
        msg_base = f"Поездка {route_dt} завершена. Оставьте отзыв участнику: "

    for from_user in participants:
        for to_user in participants:
            if from_user.id == to_user.id:
                continue
            if Rating.objects.filter(
                from_user=from_user,
                to_user=to_user,
                created_at__date=today
            ).exists():
                continue
            name = (to_user.first_name or to_user.email or "участнику").strip()
            create_notification(
                user=from_user,
                notification_type=Notification.TYPE_LEAVE_RATING,
                title=title,
                message=msg_base + name,
                trip=trip,
                target_user=to_user,
                send_email=False,
            )


def _trip_datetime_for_message(trip):
    """То же время, что в профиле (departure_datetime_display). При ошибке — пустая строка."""
    try:
        s = _departure_in_origin_tz(trip)
        return s if s else ''
    except Exception:
        return ''


def create_notification(user, notification_type, title, message, trip=None, booking=None, target_user=None, send_email=True):
    """
    Создание уведомления через Celery.

    - Сохраняет в БД
    - Публикует в Redis (для real-time на сайте)
    - Дублирует на email пользователя
    """
    create_notification_task.delay(
        user_id=user.id,
        user_email=user.email,
        user_name=user.first_name or user.email,
        notification_type=notification_type,
        title=title,
        message_text=message,
        trip_id=trip.id if trip else None,
        booking_id=booking.id if booking else None,
        target_user_id=target_user.id if target_user else None,
        send_email=send_email
    )
