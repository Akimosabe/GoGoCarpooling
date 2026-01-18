from django.conf import settings
from django.db import models
from .trip import Trip


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает подтверждения"),
        (STATUS_CONFIRMED, "Подтверждено"),
        (STATUS_REJECTED, "Отклонено водителем"),
        (STATUS_CANCELLED, "Отменено пассажиром"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="bookings")

    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    
    seats_count = models.PositiveIntegerField(default=1, help_text="Количество мест")

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED
    )
    
    # Комментарий пассажира при бронировании
    comment = models.TextField(blank=True, null=True, help_text="Комментарий пассажира")
    
    # Причина отклонения водителем
    rejection_reason = models.TextField(blank=True, null=True, help_text="Причина отклонения")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Бронирование #{self.id} – {self.passenger} ({self.trip})"
    
    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "3. Бронирования"
        unique_together = ['trip', 'passenger']  # Один пассажир = одно бронирование на поездку
