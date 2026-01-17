from django.db import models


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
