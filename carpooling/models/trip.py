from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .car import Car


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
    
    car = models.ForeignKey(
        Car, on_delete=models.SET_NULL, null=True, blank=True, related_name="trips"
    )

    origin = models.CharField(max_length=255, help_text="Откуда")
    destination = models.CharField(max_length=255, help_text="Куда")
    departure_datetime = models.DateTimeField(help_text="Дата и время отправления")

    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Цена за место")

    total_seats = models.PositiveIntegerField(
        help_text="Всего мест",
        validators=[MinValueValidator(1), MaxValueValidator(9)]
    )
    available_seats = models.PositiveIntegerField(
        help_text="Доступно мест",
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )

    # Дополнительная информация
    description = models.TextField(blank=True, null=True, help_text="Описание поездки")
    
    # Настройки поездки
    smoking_allowed = models.BooleanField(default=False, help_text="Можно курить")
    pets_allowed = models.BooleanField(default=False, help_text="Можно с животными")
    luggage_size = models.CharField(
        max_length=20,
        choices=[('small', 'Малый'), ('medium', 'Средний'), ('large', 'Большой')],
        default='medium',
        help_text="Размер багажа"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.departure_datetime})"
    
    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"
        ordering = ['-departure_datetime']
