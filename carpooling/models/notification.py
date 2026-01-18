from django.conf import settings
from django.db import models
from .trip import Trip
from .booking import Booking


class Notification(models.Model):
    """Уведомления пользователей"""
    TYPE_BOOKING_NEW = "booking_new"
    TYPE_BOOKING_CONFIRMED = "booking_confirmed"
    TYPE_BOOKING_REJECTED = "booking_rejected"
    TYPE_BOOKING_CANCELLED = "booking_cancelled"
    TYPE_TRIP_CANCELLED = "trip_cancelled"
    TYPE_TRIP_UPDATED = "trip_updated"
    
    TYPE_CHOICES = [
        (TYPE_BOOKING_NEW, "Новое бронирование"),
        (TYPE_BOOKING_CONFIRMED, "Бронирование подтверждено"),
        (TYPE_BOOKING_REJECTED, "Бронирование отклонено"),
        (TYPE_BOOKING_CANCELLED, "Бронирование отменено"),
        (TYPE_TRIP_CANCELLED, "Поездка отменена"),
        (TYPE_TRIP_UPDATED, "Поездка обновлена"),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Связь с сущностями
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} для {self.user}"
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "6. Уведомления"
        ordering = ['-created_at']
