from django.conf import settings
from django.db import models


class Car(models.Model):
    """Информация об автомобиле водителя"""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="cars",
        verbose_name="Владелец"
    )
    
    brand = models.CharField(max_length=100, verbose_name="Марка")
    model = models.CharField(max_length=100, verbose_name="Модель")
    year = models.PositiveIntegerField(verbose_name="Год выпуска")
    color = models.CharField(max_length=50, verbose_name="Цвет")
    license_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Гос. номер")
    
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    
    def __str__(self):
        if self.license_plate:
            return f"{self.brand} {self.model} ({self.license_plate})"
        return f"{self.brand} {self.model}"
    
    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"
