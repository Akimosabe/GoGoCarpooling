from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import redis
import json

from carpooling.email_templates import (
    PASSWORD_RESET_SUBJECT,
    PASSWORD_RESET_MESSAGE,
    NOTIFICATION_SUBJECT_TEMPLATE,
    NOTIFICATION_MESSAGE_TEMPLATE,
    BOOKING_CREATED_EMAIL_HTML_TEMPLATE,
)


# Redis клиент для публикации уведомлений
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list, html_message=None):
    """
    Асинхронная отправка email через Celery.
    Если передан html_message, письмо уходит в формате multipart (text + html).
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        return f"Email отправлен на {recipient_list}"
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True)
def send_password_reset_email(self, user_email, user_name, reset_link):
    """
    Отправка письма для восстановления пароля (сразу из этой задачи, без вложенной).
    Ошибки SMTP будут видны в логах Celery.
    """
    subject = PASSWORD_RESET_SUBJECT
    message = PASSWORD_RESET_MESSAGE.format(
        user_name=user_name,
        reset_link=reset_link
    )
    try:
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f"Письмо восстановления пароля отправлено на {user_email}"
    except Exception as exc:
        # Логируем и пробрасываем — в консоли Celery будет виден traceback
        raise exc


@shared_task
def create_notification_task(user_id, user_email, user_name, notification_type, title, message_text,
                              trip_id=None, booking_id=None, target_user_id=None, send_email=True):
    """
    Асинхронное создание уведомления:
    1. Сохраняет в БД
    2. Публикует в Redis (для real-time на фронте)
    3. Отправляет дубликат на email
    """
    from carpooling.models import Notification, Trip, Booking, User

    # Получаем объекты
    user = User.objects.get(id=user_id)
    trip = Trip.objects.get(id=trip_id) if trip_id else None
    booking = Booking.objects.get(id=booking_id) if booking_id else None
    target_user = User.objects.get(id=target_user_id) if target_user_id else None

    # 1. Сохраняем в БД
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message_text,
        trip=trip,
        booking=booking,
        target_user=target_user
    )

    # 2. Публикуем в Redis для real-time уведомлений
    notification_data = {
        'id': notification.id,
        'type': notification_type,
        'title': title,
        'message': message_text,
        'trip_id': trip_id,
        'booking_id': booking_id,
        'target_user_id': target_user_id,
        'is_read': False,
        'created_at': notification.created_at.isoformat()
    }
    
    # Публикуем в канал пользователя
    channel = f"notifications:user:{user_id}"
    redis_client.publish(channel, json.dumps(notification_data, ensure_ascii=False))
    
    # Также сохраняем в список непрочитанных (для polling если WebSocket недоступен)
    redis_client.lpush(f"notifications:unread:{user_id}", json.dumps(notification_data, ensure_ascii=False))
    redis_client.ltrim(f"notifications:unread:{user_id}", 0, 99)  # Храним последние 100
    
    # 3. Отправляем дубликат на email
    if send_email and user_email:
        subject = NOTIFICATION_SUBJECT_TEMPLATE.format(title=title)
        html_message = None
        if notification_type == Notification.TYPE_BOOKING_CREATED and trip:
            from carpooling.serializers.trip import _departure_in_origin_tz
            trip_link = f"{settings.FRONTEND_URL}/trips/{trip.id}"
            dt_str = _departure_in_origin_tz(trip) or ""
            link_text = f"{trip.origin.name} → {trip.destination.name}"
            if dt_str:
                link_text += f" ({dt_str})"
            driver_name = (trip.driver.first_name or trip.driver.email or "водитель").strip()
            html_message = BOOKING_CREATED_EMAIL_HTML_TEMPLATE.format(
                user_name=user_name,
                trip_link=trip_link,
                link_text=link_text,
                driver_name=driver_name,
            ).strip()
            plain_message = NOTIFICATION_MESSAGE_TEMPLATE.format(
                user_name=user_name,
                message=message_text
            ).strip()
        else:
            plain_message = NOTIFICATION_MESSAGE_TEMPLATE.format(
                user_name=user_name,
                message=message_text
            ).strip()
        send_email_task.delay(subject, plain_message, [user_email], html_message=html_message)
    return f"Уведомление #{notification.id} создано для пользователя {user_id}"


@shared_task
def send_booking_notifications_task(booking_id):
    """
    После создания бронирования: уведомление водителю и пассажиру (в приложении + email).
    Вызывается из view через .delay(), чтобы не задерживать ответ пользователю.
    """
    from carpooling.models import Booking, Notification
    from carpooling.serializers.trip import _departure_in_origin_tz

    booking = Booking.objects.select_related(
        "trip", "trip__origin", "trip__destination", "trip__driver", "passenger"
    ).get(id=booking_id)
    trip = booking.trip
    seats_count = booking.seats_count
    passenger = booking.passenger
    driver = trip.driver

    route = f"{trip.origin.name} → {trip.destination.name}"
    dt_str = _departure_in_origin_tz(trip) or ""
    seats_word = "место" if seats_count == 1 else "места" if 2 <= seats_count <= 4 else "мест"
    msg_driver = f"{passenger.first_name or passenger.email} забронировал {seats_count} {seats_word} в поездке {route}"
    if dt_str:
        msg_driver += f" ({dt_str})"

    create_notification_task.delay(
        user_id=driver.id,
        user_email=driver.email or "",
        user_name=(driver.first_name or driver.email or "").strip(),
        notification_type=Notification.TYPE_BOOKING_NEW,
        title="Новое бронирование",
        message_text=msg_driver,
        trip_id=trip.id,
        booking_id=booking.id,
        target_user_id=None,
        send_email=True,
    )

    driver_name = (driver.first_name or driver.email or "водитель").strip()
    route_dt = f"{route}" + (f" ({dt_str})" if dt_str else "")
    msg_passenger = f"Вы забронировали поездку {route_dt} у водителя {driver_name}."
    create_notification_task.delay(
        user_id=passenger.id,
        user_email=passenger.email or "",
        user_name=(passenger.first_name or passenger.email or "").strip(),
        notification_type=Notification.TYPE_BOOKING_CREATED,
        title="Бронирование оформлено",
        message_text=msg_passenger,
        trip_id=trip.id,
        booking_id=booking.id,
        target_user_id=None,
        send_email=True,
    )
    return f"Уведомления по бронированию #{booking_id} отправлены"


@shared_task
def send_notification_email(user_email, user_name, title, message_text):
    """
    Отправка email-уведомления пользователю (legacy, для обратной совместимости).
    """
    subject = NOTIFICATION_SUBJECT_TEMPLATE.format(title=title)
    message = NOTIFICATION_MESSAGE_TEMPLATE.format(
        user_name=user_name,
        message=message_text
    )
    
    return send_email_task.delay(subject, message.strip(), [user_email])
