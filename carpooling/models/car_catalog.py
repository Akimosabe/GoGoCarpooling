from django.db import models


class CarCatalog(models.Model):
    """
    Справочник марок и моделей авто (латиница).
    Заполняется парсингом (NHTSA/GitHub) и вручную в админке.
    Используется для подсказки при выборе марки/модели (по первым символам);
    в автомобиль пользователя передаётся строка, старые данные не ломаются.
    """
    make = models.CharField(max_length=120, db_index=True, verbose_name="Марка")
    model = models.CharField(max_length=120, db_index=True, verbose_name="Модель")

    class Meta:
        verbose_name = "Марка/модель"
        verbose_name_plural = "7. Автомобили"
        ordering = ['make', 'model']
        unique_together = [['make', 'model']]
        indexes = [
            models.Index(fields=['make', 'model']),
        ]

    def __str__(self):
        return f"{self.make} {self.model}"
