from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


class UserProfile(models.Model):
    """Профиль пользователя с дополнительной информацией"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="О себе")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Статистика
    trips_as_driver = models.PositiveIntegerField(default=0)
    trips_as_passenger = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.user.username}"
    
    @property
    def average_rating(self):
        """Средний рейтинг пользователя"""
        avg = self.received_ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 0
    
    @property
    def total_ratings_count(self):
        """Количество полученных оценок"""
        return self.received_ratings.count()


class Car(models.Model):
    """Информация об автомобиле водителя"""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cars"
    )
    
    brand = models.CharField(max_length=100, help_text="Марка")
    model = models.CharField(max_length=100, help_text="Модель")
    year = models.PositiveIntegerField(help_text="Год выпуска")
    color = models.CharField(max_length=50, help_text="Цвет")
    license_plate = models.CharField(max_length=20, help_text="Гос. номер")
    
    is_active = models.BooleanField(default=True, help_text="Активный автомобиль")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"
    
    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"


class City(models.Model):
    """База городов для поиска"""
    name = models.CharField(max_length=200, unique=True)
    region = models.CharField(max_length=200, help_text="Область/Регион")
    country = models.CharField(max_length=100, default="Россия")
    
    # Координаты для будущего функционала карты
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    is_popular = models.BooleanField(default=False, help_text="Популярный город")
    
    def __str__(self):
        return f"{self.name}, {self.region}"
    
    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ['name']


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

    total_seats = models.PositiveIntegerField(help_text="Всего мест")
    available_seats = models.PositiveIntegerField(help_text="Доступно мест")

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
        return f"Booking #{self.id} – {self.passenger.username} ({self.trip})"
    
    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        unique_together = ['trip', 'passenger']  # Один пассажир = одно бронирование на поездку


class Rating(models.Model):
    """Рейтинги и отзывы пользователей"""
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="ratings"
    )
    
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_ratings"
    )
    
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_ratings"
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка от 1 до 5"
    )
    
    comment = models.TextField(blank=True, null=True, help_text="Комментарий")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rating {self.rating}/5: {self.from_user} → {self.to_user}"
    
    class Meta:
        verbose_name = "Рейтинг"
        verbose_name_plural = "Рейтинги"
        unique_together = ['trip', 'from_user', 'to_user']


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
        return f"{self.title} для {self.user.username}"
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']
