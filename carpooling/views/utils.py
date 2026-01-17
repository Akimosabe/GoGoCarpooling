from carpooling.models import Notification


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
