from django.conf import settings
from django.db import models
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
