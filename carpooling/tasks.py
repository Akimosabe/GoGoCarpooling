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
)


# Redis клиент для публикации уведомлений
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list):
    """
    Асинхронная отправка email через Celery.
    
    При ошибке повторяет попытку 3 раза с интервалом 60 секунд.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Email отправлен на {recipient_list}"
    except Exception as exc:
        # Повторяем попытку при ошибке
        raise self.retry(exc=exc)


@shared_task
def send_password_reset_email(user_email, user_name, reset_link):
    """
    Отправка письма для восстановления пароля.
    """
    subject = PASSWORD_RESET_SUBJECT
    message = PASSWORD_RESET_MESSAGE.format(
        user_name=user_name,
        reset_link=reset_link
    )
    
    return send_email_task.delay(subject, message.strip(), [user_email])


@shared_task
def create_notification_task(user_id, user_email, user_name, notification_type, title, message_text, 
                              trip_id=None, booking_id=None, send_email=True):
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
    
    # 1. Сохраняем в БД
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message_text,
        trip=trip,
        booking=booking
    )
    
    # 2. Публикуем в Redis для real-time уведомлений
    notification_data = {
        'id': notification.id,
        'type': notification_type,
        'title': title,
        'message': message_text,
        'trip_id': trip_id,
        'booking_id': booking_id,
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
        email_message = NOTIFICATION_MESSAGE_TEMPLATE.format(
            user_name=user_name,
            message=message_text
        )
        send_email_task.delay(subject, email_message.strip(), [user_email])
    
    return f"Уведомление #{notification.id} создано для пользователя {user_id}"


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
