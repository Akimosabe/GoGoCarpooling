from django.db import models


# Часовые пояса России
RUSSIA_TIMEZONES = [
    ('Europe/Kaliningrad', 'Калининград (UTC+2)'),
    ('Europe/Moscow', 'Москва (UTC+3)'),
    ('Europe/Samara', 'Самара (UTC+4)'),
    ('Asia/Yekaterinburg', 'Екатеринбург (UTC+5)'),
    ('Asia/Omsk', 'Омск (UTC+6)'),
    ('Asia/Krasnoyarsk', 'Красноярск (UTC+7)'),
    ('Asia/Irkutsk', 'Иркутск (UTC+8)'),
    ('Asia/Yakutsk', 'Якутск (UTC+9)'),
    ('Asia/Vladivostok', 'Владивосток (UTC+10)'),
    ('Asia/Magadan', 'Магадан (UTC+11)'),
    ('Asia/Kamchatka', 'Камчатка (UTC+12)'),
]


class City(models.Model):
    """База городов для поиска (данные из GeoNames)"""
    
    # GeoNames ID для избежания дубликатов при повторном импорте
    geoname_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    
    name = models.CharField(max_length=200, db_index=True, verbose_name="Название")
    region = models.CharField(max_length=200, db_index=True, verbose_name="Область/Регион")
    country = models.CharField(max_length=100, default="Россия", db_index=True, verbose_name="Страна")
    country_code = models.CharField(max_length=2, default="RU", verbose_name="ISO код страны")
    
    # Часовой пояс города
    timezone = models.CharField(
        max_length=50,
        choices=RUSSIA_TIMEZONES,
        default='Europe/Moscow',
        verbose_name="Часовой пояс"
    )
    
    # Координаты для будущего функционала карты
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Долгота")
    
    # Население для сортировки (крупные города выше)
    population = models.IntegerField(default=0, db_index=True, verbose_name="Население")
    
    is_popular = models.BooleanField(default=False, verbose_name="Популярный город")
    
    def __str__(self):
        return f"{self.name}, {self.region}"
    
    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "5. Города"
        ordering = ['-population', 'name']
        # Уникальность по названию + региону + стране (могут быть одинаковые названия в разных регионах)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'region', 'country'],
                name='unique_city_region_country'
            )
        ]
