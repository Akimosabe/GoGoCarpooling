from django.conf import settings
from django.db import models


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
