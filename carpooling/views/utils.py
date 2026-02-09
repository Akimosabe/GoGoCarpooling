from carpooling.tasks import create_notification_task
from carpooling.serializers.trip import _departure_in_origin_tz


def _trip_datetime_for_message(trip):
    """То же время, что в профиле (departure_datetime_display). При ошибке — пустая строка."""
    try:
        s = _departure_in_origin_tz(trip)
        return s if s else ''
    except Exception:
        return ''


def create_notification(user, notification_type, title, message, trip=None, booking=None, send_email=True):
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
        send_email=send_email
    )
