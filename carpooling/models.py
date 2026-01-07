from django.conf import settings
from django.db import models


class Trip(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Активна"),
        (STATUS_CANCELLED, "Отменена"),
        (STATUS_COMPLETED, "Завершена"),
    ]

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driven_trips"
    )

    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_datetime = models.DateTimeField()

    price = models.DecimalField(max_digits=8, decimal_places=2)

    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.departure_datetime})"


class Booking(models.Model):
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_CONFIRMED, "Подтверждено"),
        (STATUS_CANCELLED, "Отменено"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="bookings")

    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} – {self.passenger}"
