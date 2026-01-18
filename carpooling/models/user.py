from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Avg
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User"""
    
    def create_user(self, email, phone=None, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError('Email обязателен')
        
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')
        
        return self.create_user(email, password=password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя"""
    
    # Убираем username, используем email для входа
    username = None
    first_name = models.CharField(
        max_length=150, 
        blank=True,
        verbose_name="Имя"
    )
    last_name = None  # Убираем фамилию
    
    email = models.EmailField(
        unique=True,
        verbose_name="Email"
    )
    
    phone = models.CharField(
        max_length=20, 
        blank=True,
        null=True,
        verbose_name="Телефон"
    )
    
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True,
        verbose_name="Аватар"
    )
    
    date_of_birth = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Дата рождения"
    )
    
    # Статистика
    trips_as_driver = models.PositiveIntegerField(
        default=0,
        verbose_name="Поездок как водитель"
    )
    trips_as_passenger = models.PositiveIntegerField(
        default=0,
        verbose_name="Поездок как пассажир"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email уже включен как USERNAME_FIELD
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "1. Пользователи"
    
    def __str__(self):
        if self.first_name:
            return f"{self.first_name} ({self.email})"
        return self.email
    
    def clean(self):
        """Валидация: для обычных пользователей обязательны phone, email, first_name"""
        super().clean()
        
        # Для админов и суперюзеров поля не обязательны
        if self.is_staff or self.is_superuser:
            return
        
        errors = {}
        
        if not self.phone:
            errors['phone'] = 'Телефон обязателен для обычных пользователей'
        
        if not self.first_name:
            errors['first_name'] = 'Имя обязательно для обычных пользователей'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Вызываем clean() при сохранении
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        """Средний рейтинг пользователя"""
        avg = self.received_ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 0
    
    @property
    def total_ratings_count(self):
        """Количество полученных оценок"""
        return self.received_ratings.count()
