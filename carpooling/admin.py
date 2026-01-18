from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as AuthGroup
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from datetime import datetime
import pytz
from .models import User, Car, City, Trip, Booking, Rating, Notification, Group


# Убираем стандартный раздел Group из auth
admin.site.unregister(AuthGroup)


class CarAdmin(admin.ModelAdmin):
    """Админка для автомобилей (нужна для autocomplete, скрыта из меню)"""
    search_fields = ['brand', 'model', 'license_plate', 'owner__email', 'owner__first_name']
    
    def has_module_permission(self, request):
        """Скрываем из главного меню админки"""
        return False

# Регистрируем для работы autocomplete
admin.site.register(Car, CarAdmin)


class CarInline(admin.TabularInline):
    """Инлайн для автомобилей пользователя"""
    model = Car
    extra = 0
    fields = ['brand', 'model', 'year', 'color', 'license_plate', 'is_active']
    verbose_name = "Автомобиль"
    verbose_name_plural = "Автомобили"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Кастомная админка для пользователей"""
    
    list_display = [
        'id', 'email', 'first_name', 'phone', 'is_staff', 
        'get_trips_as_driver', 'get_trips_as_passenger', 'average_rating', 'created_at'
    ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'created_at']
    search_fields = ['id', 'email', 'first_name', 'phone']
    ordering = ['-created_at']
    list_per_page = 25
    
    inlines = [CarInline]
    
    # Поля для редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'password')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'phone', 'avatar', 'date_of_birth')
        }),
        ('Статистика поездок', {
            'fields': ('get_trips_as_driver', 'get_trips_as_passenger', 'user_trips_link', 'user_bookings_link'),
        }),
        ('Рейтинг', {
            'fields': ('average_rating', 'total_ratings_count', 'user_ratings_link'),
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'phone', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = [
        'created_at', 'updated_at', 'last_login', 
        'get_trips_as_driver', 'get_trips_as_passenger',
        'average_rating', 'total_ratings_count',
        'user_trips_link', 'user_bookings_link', 'user_ratings_link'
    ]
    
    def get_trips_as_driver(self, obj):
        """Количество завершённых поездок как водитель"""
        return obj.trips_as_driver
    get_trips_as_driver.short_description = "Поездок (водитель)"
    
    def get_trips_as_passenger(self, obj):
        """Количество завершённых поездок как пассажир"""
        return obj.trips_as_passenger
    get_trips_as_passenger.short_description = "Поездок (пассажир)"
    
    def user_trips_link(self, obj):
        """Ссылка на поездки пользователя"""
        url = reverse('admin:carpooling_trip_changelist') + f'?driver__id__exact={obj.id}'
        count = obj.driven_trips.count()
        return format_html('<a href="{}">Поездки как водитель ({})</a>', url, count)
    user_trips_link.short_description = "Поездки"
    
    def user_bookings_link(self, obj):
        """Ссылка на бронирования пользователя"""
        url = reverse('admin:carpooling_booking_changelist') + f'?passenger__id__exact={obj.id}'
        count = obj.bookings.count()
        return format_html('<a href="{}">Бронирования ({})</a>', url, count)
    user_bookings_link.short_description = "Бронирования"
    
    def user_ratings_link(self, obj):
        """Ссылка на оценки пользователя"""
        url = reverse('admin:carpooling_rating_changelist') + f'?to_user__id__exact={obj.id}'
        count = obj.received_ratings.count()
        return format_html('<a href="{}">Полученные оценки ({})</a>', url, count)
    user_ratings_link.short_description = "Оценки"


class TripAdminForm(forms.ModelForm):
    """
    Форма для админки поездок с валидацией и конвертацией времени 
    по часовому поясу города отправления.
    
    Время в админке вводится как ЛОКАЛЬНОЕ ВРЕМЯ ГОРОДА ОТПРАВЛЕНИЯ,
    а не как московское время.
    """
    
    MAX_SEATS = 9  # Максимальное количество мест в поездке
    
    # Переопределяем поля с ограничениями на уровне виджета
    total_seats = forms.IntegerField(
        min_value=1,
        max_value=9,
        label='Всего мест',
        widget=forms.NumberInput(attrs={'min': 1, 'max': 9})
    )
    available_seats = forms.IntegerField(
        min_value=0,
        max_value=9,
        label='Доступно мест',
        widget=forms.NumberInput(attrs={'min': 0, 'max': 9})
    )
    
    class Meta:
        model = Trip
        fields = '__all__'
    
    class Media:
        js = ('admin/js/trip_seats.js',)
    
    def clean_total_seats(self):
        """Валидация общего количества мест"""
        total_seats = self.cleaned_data.get('total_seats')
        if total_seats is not None:
            if total_seats < 1:
                raise forms.ValidationError('Количество мест должно быть не менее 1')
            if total_seats > self.MAX_SEATS:
                raise forms.ValidationError(f'Количество мест не может превышать {self.MAX_SEATS}')
        return total_seats
    
    def clean_available_seats(self):
        """Валидация доступных мест"""
        available_seats = self.cleaned_data.get('available_seats')
        if available_seats is not None:
            if available_seats < 0:
                raise forms.ValidationError('Количество доступных мест не может быть отрицательным')
            if available_seats > self.MAX_SEATS:
                raise forms.ValidationError(f'Количество доступных мест не может превышать {self.MAX_SEATS}')
        return available_seats
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Валидация: доступных мест не может быть больше общего количества
        total_seats = cleaned_data.get('total_seats')
        available_seats = cleaned_data.get('available_seats')
        
        if total_seats is not None and available_seats is not None:
            if available_seats > total_seats:
                raise forms.ValidationError(
                    'Доступных мест не может быть больше общего количества мест'
                )
        
        origin = cleaned_data.get('origin')
        departure_datetime = cleaned_data.get('departure_datetime')
        
        if origin and departure_datetime:
            # Получаем часовой пояс города отправления
            origin_tz = pytz.timezone(origin.timezone)
            server_tz = pytz.timezone('Europe/Moscow')  # TIME_ZONE из settings
            now_utc = datetime.now(pytz.UTC)
            
            # Django админка конвертирует введённое время в UTC, 
            # предполагая что оно было в TIME_ZONE (Москва).
            # Нам нужно "отменить" эту конвертацию и применить правильный часовой пояс.
            
            if departure_datetime.tzinfo is not None:
                # Время уже aware (Django сконвертировал из московского в UTC)
                # Конвертируем обратно в "московское" чтобы получить введённые цифры
                moscow_time = departure_datetime.astimezone(server_tz)
                # Теперь интерпретируем эти цифры как время города отправления
                naive_time = moscow_time.replace(tzinfo=None)
                local_time = origin_tz.localize(naive_time)
                departure_utc = local_time.astimezone(pytz.UTC)
            else:
                # Если naive - локализуем как время города отправления
                local_time = origin_tz.localize(departure_datetime)
                departure_utc = local_time.astimezone(pytz.UTC)
            
            # Проверяем, что время не в прошлом
            if departure_utc < now_utc:
                now_local = now_utc.astimezone(origin_tz)
                raise forms.ValidationError(
                    f'Нельзя публиковать поездку в прошлом. '
                    f'Текущее время в {origin.name}: {now_local.strftime("%d.%m.%Y %H:%M")}'
                )
            
            # Сохраняем правильно сконвертированное время
            cleaned_data['departure_datetime'] = departure_utc
        
        return cleaned_data


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    form = TripAdminForm
    list_display = [
        'id', 'driver', 'origin', 'destination', 'departure_datetime',
        'price', 'available_seats', 'total_seats', 'status', 'created_at'
    ]
    list_filter = ['status', 'departure_datetime', 'created_at', 'origin', 'destination']
    search_fields = ['driver__email', 'driver__first_name', 'origin__name', 'destination__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'departure_datetime'
    ordering = ['-departure_datetime']
    autocomplete_fields = ['driver', 'car', 'origin', 'destination']
    list_per_page = 25
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('driver', 'car', 'status')
        }),
        ('Маршрут', {
            'fields': ('origin', 'destination', 'departure_datetime')
        }),
        ('Места и цена', {
            'fields': ('total_seats', 'available_seats', 'price')
        }),
        ('Дополнительно', {
            'fields': ('description', 'smoking_allowed', 'pets_allowed', 'luggage_size')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'trip', 'passenger', 'seats_count', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['passenger__email', 'passenger__first_name', 'trip__origin', 'trip__destination']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['trip', 'passenger']
    list_per_page = 25
    
    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('trip', 'passenger', 'seats_count', 'status')
        }),
        ('Комментарии', {
            'fields': ('comment', 'rejection_reason')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'rating', 'trip', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['from_user__email', 'to_user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['trip', 'from_user', 'to_user']
    list_per_page = 25


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'country', 'is_popular']
    search_fields = ['name', 'region']
    list_filter = ['is_popular', 'country']
    ordering = ['-population', 'name']
    list_per_page = 50  # Городов много, показываем больше


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['user', 'trip', 'booking']
    list_per_page = 50  # Уведомлений много
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} уведомлений отмечено как прочитанные')
    mark_as_read.short_description = 'Отметить как прочитанные'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} уведомлений отмечено как непрочитанные')
    mark_as_unread.short_description = 'Отметить как непрочитанные'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Админка для групп пользователей"""
    list_display = ['name']
    search_fields = ['name']
    filter_horizontal = ['permissions']
