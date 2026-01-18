from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .car import Car
from .city import City


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
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="driven_trips",
        verbose_name="Водитель"
    )
    
    car = models.ForeignKey(
        Car, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="trips",
        verbose_name="Автомобиль"
    )

    origin = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="trips_from",
        verbose_name="Откуда"
    )
    destination = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="trips_to",
        verbose_name="Куда"
    )
    departure_datetime = models.DateTimeField(verbose_name="Дата и время отправления")

    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Цена за место"
    )

    total_seats = models.PositiveIntegerField(
        verbose_name="Всего мест",
        validators=[MinValueValidator(1), MaxValueValidator(9)]
    )
    available_seats = models.PositiveIntegerField(
        verbose_name="Доступно мест",
        validators=[MinValueValidator(0), MaxValueValidator(9)]
    )

    # Дополнительная информация
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Описание поездки"
    )
    
    # Настройки поездки
    smoking_allowed = models.BooleanField(
        default=False, 
        verbose_name="Можно курить"
    )
    pets_allowed = models.BooleanField(
        default=False, 
        verbose_name="Можно с животными"
    )
    luggage_size = models.CharField(
        max_length=20,
        choices=[('small', 'Малый'), ('medium', 'Средний'), ('large', 'Большой')],
        default='medium',
        verbose_name="Размер багажа"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_ACTIVE,
        verbose_name="Статус"
    )

    def __str__(self):
        return f"{self.origin.name} → {self.destination.name} ({self.departure_datetime})"
    
    @property
    def is_expired(self):
        """
        Проверяет, истекла ли дата поездки.
        
        departure_datetime хранится в UTC с учётом часового пояса города отправления,
        поэтому простое сравнение с timezone.now() (тоже UTC) корректно.
        """
        return self.departure_datetime < timezone.now()
    
    @property
    def effective_status(self):
        """
        Возвращает эффективный статус поездки с учетом даты.
        Если поездка активна, но дата прошла - возвращает 'completed'.
        """
        if self.status == self.STATUS_ACTIVE and self.is_expired:
            return self.STATUS_COMPLETED
        return self.status
    
    def check_and_complete_if_expired(self):
        """
        Проверяет и завершает поездку, если дата истекла.
        Возвращает True, если статус был изменен.
        """
        if self.status == self.STATUS_ACTIVE and self.is_expired:
            self.status = self.STATUS_COMPLETED
            self.save(update_fields=['status'])
            return True
        return False
    
    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "2. Поездки"
        ordering = ['-departure_datetime']
        indexes = [
            # Индекс для автозакрытия просроченных поездок (команда complete_expired_trips)
            # и для поиска активных поездок в будущем (trip_list view)
            models.Index(fields=['status', 'departure_datetime'], name='trip_status_departure_idx'),
        ]
