from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .trip import Trip


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
        return f"Оценка {self.rating}/5: {self.from_user} → {self.to_user}"
    
    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "4. Оценки"
        unique_together = ['trip', 'from_user', 'to_user']
